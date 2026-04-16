from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.schematic import render_schematic_svg
from app.schema.simulation import SchematicResult


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_output_filename() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"schematic_{stamp}_{uuid4().hex[:8]}.svg"


def generate_schematic(
    netlist: str,
    *,
    save_to_project_root: bool = False,
) -> SchematicResult:
    svg = render_schematic_svg(netlist)
    saved_path = None

    if save_to_project_root:
        output_path = _project_root() / _build_output_filename()
        output_path.write_text(svg, encoding="utf-8")
        saved_path = str(output_path)

    return SchematicResult(format="svg", content=svg, saved_path=saved_path)
