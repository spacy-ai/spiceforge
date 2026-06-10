from __future__ import annotations

import os
import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

from app.services.netlist_to_schemdraw import (
    parse_netlist,
    analyse_topology,
    emit_code,
)


class SVGRenderer(ABC):
    @abstractmethod
    def render(self, circuit, output_path: str) -> str:
        pass


class StandardSVGRenderer(SVGRenderer):
    def render(self, circuit, output_path: str) -> str:
        code = emit_code(circuit)
        return _render_svg(code, output_path)


class InteractiveSVGRenderer(SVGRenderer):
    """
    Renders circuit SVG with a dark background, gold circuit lines, and white labels.

    Text color is set via matplotlib rcParams before rendering so that matplotlib
    emits style="fill: <text_color>" directly on glyph groups. Post-render regex
    then handles strokes and remaining fills.
    """

    def __init__(
        self,
        background_color: str = "#312c24",
        circuit_color: str = "#ffd700",
        text_color: str = "#ffffff",
    ) -> None:
        self.background_color = background_color
        self.circuit_color = circuit_color
        self.text_color = text_color

    def render(self, circuit, output_path: str) -> str:
        code = emit_code(circuit)

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            temp_path = tmp.name

        try:
            svg_content = _render_svg(code, temp_path, text_color=self.text_color)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        modified = self._transform_colors(svg_content)
        Path(output_path).write_text(modified, encoding="utf-8")
        return modified

    def _transform_colors(self, svg: str) -> str:
        fg   = self.circuit_color
        bg   = self.background_color

        result = svg

        # 1. White canvas rect → background color.
        result = re.sub(r'fill:\s*#ffffff\b',                 f'fill: {bg}', result)
        result = re.sub(r'fill:\s*rgb\(255,\s*255,\s*255\)',  f'fill: {bg}', result)

        # 2. Circuit line strokes.
        result = re.sub(r'stroke:\s*#000000\b',               f'stroke: {fg}', result)
        result = re.sub(r'stroke:\s*rgb\(0,\s*0,\s*0\)',      f'stroke: {fg}', result)

        # 3. Remaining black fills (component bodies, arrowheads, etc.).
        #    Text glyph fills are already set to text_color by rcParams at render
        #    time, so this only touches genuine circuit fills.
        result = re.sub(r'fill:\s*#000000\b',                 f'fill: {fg}', result)
        result = re.sub(r'fill:\s*rgb\(0,\s*0,\s*0\)',        f'fill: {fg}', result)

        # 4. Inject a full-size background rect immediately after the opening <svg> tag.
        bg_rect = f'<rect width="100%" height="100%" fill="{bg}"/>'
        result  = re.sub(r'(<svg[^>]*>)', r'\1' + bg_rect, result, count=1)

        return result


def _render_svg(code: str, out_path: str, text_color: str | None = None) -> str:
    """
    Execute generated schemdraw code and return SVG content as a string.

    If text_color is provided, matplotlib's text.color rcParam is set before
    rendering so that glyph groups carry an explicit fill style in the SVG output.
    rcParams are restored to defaults afterward regardless of outcome.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import schemdraw
    import schemdraw.elements as elm

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    exec_code = code.replace(
        "with schemdraw.Drawing() as d:",
        f"with schemdraw.Drawing(file={str(out)!r}, show=False) as d:",
        1,
    )

    if text_color:
        plt.rcParams["text.color"] = text_color

    try:
        exec(exec_code, {"schemdraw": schemdraw, "elm": elm}, {})
    finally:
        if text_color:
            plt.rcParams.update(plt.rcParamsDefault)

    if not out.exists():
        raise RuntimeError(f"Failed to generate SVG at {out_path}")

    return out.read_text(encoding="utf-8")


def render_both_svgs(
    netlist_text: str,
    output_dir: str | None = None,
    unit: int = 3,
) -> Dict[str, str]:
    elements = parse_netlist(netlist_text)
    circuit  = analyse_topology(elements)

    out = Path(output_dir or "./svg_exports")
    out.mkdir(parents=True, exist_ok=True)

    std_path = out / "schematic_standard.svg"
    StandardSVGRenderer().render(circuit, str(std_path))

    int_path = out / "schematic_interactive.svg"
    InteractiveSVGRenderer(
        background_color="#1a1a2e",
        circuit_color="#ffd700",
        text_color="#ffffff",
    ).render(circuit, str(int_path))

    return {
        "standard": str(std_path),
        "interactive": str(int_path),
    }