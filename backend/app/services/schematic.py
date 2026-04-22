from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import uuid4

from app.core.interactive_svg import render_interactive_svg
from app.core.schematic import render_schematic_svg
from app.schema.simulation import SchematicResult


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_output_filename() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"schematic_{stamp}_{uuid4().hex[:8]}.svg"


@lru_cache(maxsize=128)
def _render_interactive_cached(netlist: str, width: int, height: int) -> str:
    return render_interactive_svg(netlist, width=width, height=height)


def generate_schematic(
    netlist: str,
    *,
    save_to_project_root: bool = False,
    renderer: Literal["schemdraw", "interactive"] = "schemdraw",
    width: int = 800,
    height: int = 600,
) -> SchematicResult:
    if renderer == "interactive":
        svg = _render_interactive_cached(netlist, width, height)
    else:
        svg = render_schematic_svg(netlist)
    saved_path = None

    if save_to_project_root:
        output_path = _project_root() / _build_output_filename()
        output_path.write_text(svg, encoding="utf-8")
        saved_path = str(output_path)

    return SchematicResult(format="svg", content=svg, saved_path=saved_path)
