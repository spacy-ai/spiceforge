from __future__ import annotations

import tempfile
from pathlib import Path

from app.core.kicad_export import export_kicad_schematic
from app.core.sanitize import validate_filename
from app.services.export_store import export_store, ExportRecord


def create_kicad_export(
    *, netlist: str, filename: str | None, user_id: int
) -> tuple[ExportRecord, list[str]]:
    if filename is None or not filename.strip():
        filename = "circuit.kicad_sch"
    validate_filename(filename)

    output_dir = Path(tempfile.mkdtemp(prefix="spice_platform_export_"))
    output_path, warnings = export_kicad_schematic(
        netlist,
        output_dir=output_dir,
        filename=filename,
    )
    record = export_store.create(file_path=output_path, user_id=user_id)
    return record, warnings
