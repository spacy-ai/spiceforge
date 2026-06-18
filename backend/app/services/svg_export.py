from __future__ import annotations

import uuid
import os
import tempfile
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.services.netlist_to_schemdraw import parse_netlist, analyse_topology
from app.services.interactive_svg import StandardSVGRenderer, InteractiveSVGRenderer
from app.models.svg_export import SvgExport

load_dotenv()

EXPORT_EXPIRY_DAYS = int(os.getenv("EXPORT_EXPIRY_DAYS", "7"))


class ExportStore:
    def __init__(self, db: Session):
        self.db = db

    def create_record(
        self,
        content: str,
        format: str = "interactive",
        circuit_id: int | None = None,
        user_id: int | None = None,
        extra_data: dict | None = None,
    ) -> SvgExport:
        export_id = str(uuid.uuid4())

        db_export = SvgExport(
            export_id=export_id,
            circuit_id=circuit_id,
            content=content,
            format=format,
            user_id=user_id,
            expires_at=datetime.now() + timedelta(days=EXPORT_EXPIRY_DAYS),
            extra_data=str(extra_data) if extra_data else None,
        )

        self.db.add(db_export)
        self.db.commit()
        self.db.refresh(db_export)
        return db_export

    def get_record(self, export_id: str) -> SvgExport | None:
        return (
            self.db.query(SvgExport)
            .filter(SvgExport.export_id == export_id)
            .first()
        )

    def get_content(self, export_id: str) -> str | None:
        record = self.get_record(export_id)
        return record.content if record else None

    def cleanup_expired(self) -> int:
        expired = (
            self.db.query(SvgExport)
            .filter(SvgExport.expires_at < datetime.now())
            .all()
        )
        count = len(expired)
        for export in expired:
            self.db.delete(export)
        self.db.commit()
        return count


def create_svg_export(
    db: Session,
    netlist: str,
    format: str = "interactive",
    circuit_id: int | None = None,
    filename: str | None = None,
    highlight_color: str = "#ffd700",
    highlight_opacity: float = 0.8,
    hover_stroke_width: int = 2,
    user_id: int | None = None,
) -> tuple[SvgExport, list[str]]:
    warnings: list[str] = []

    try:
        elements = parse_netlist(netlist)
        circuit  = analyse_topology(elements)
    except Exception as e:
        raise ValueError(f"Failed to parse netlist: {e}")

    try:
        if format == "interactive":
            renderer = InteractiveSVGRenderer(
                background_color="#1a1814",
                circuit_color=highlight_color,
                text_color="#ffffff",
            )
        else:
            renderer = StandardSVGRenderer()

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            temp_path = tmp.name

        try:
            content = renderer.render(circuit, temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        raise ValueError(f"Failed to render SVG: {e}")

    record = ExportStore(db).create_record(
        content=content,
        format=format,
        circuit_id=circuit_id,
        user_id=user_id,
        extra_data={"warnings": warnings},
    )

    return record, warnings