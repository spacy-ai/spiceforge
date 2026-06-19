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
        fg = self.circuit_color
        bg = self.background_color
        text_color = self.text_color

        result = svg

        # 1. Remove existing background rectangles
        result = re.sub(r'<rect[^>]*width="100%"[^>]*height="100%"[^>]*fill="[^"]*"[^>]*>', '', result)
        result = re.sub(r'<rect[^>]*fill="[^"]*"[^>]*width="100%"[^>]*height="100%"[^>]*>', '', result)

        # 2. Handle text elements - force text color
        # For <text> elements with fill attribute
        result = re.sub(
            r'(<text[^>]*?)fill="[^"]*"',
            rf'\1fill="{text_color}"',
            result
        )
        # For <text> elements with style containing fill
        result = re.sub(
            r'(<text[^>]*?style="[^"]*?)fill:[^;"]*',
            rf'\1fill:{text_color}',
            result
        )
        # For <text> elements without fill
        result = re.sub(
            r'(<text)(?!.*fill=)',
            rf'\1 fill="{text_color}"',
            result
        )
        
        # Same for tspan elements
        result = re.sub(
            r'(<tspan[^>]*?)fill="[^"]*"',
            rf'\1fill="{text_color}"',
            result
        )
        result = re.sub(
            r'(<tspan[^>]*?style="[^"]*?)fill:[^;"]*',
            rf'\1fill:{text_color}',
            result
        )
        result = re.sub(
            r'(<tspan)(?!.*fill=)',
            rf'\1 fill="{text_color}"',
            result
        )

        # 3. Handle text path groups (when matplotlib converts text to paths)
        # Find text groups and change their fill color
        def replace_text_path_fill(match):
            group_content = match.group(0)
            # Change fill in style
            group_content = re.sub(
                r'style="[^"]*?fill:#[0-9a-fA-F]{6}',
                f'style="fill:{text_color}',
                group_content
            )
            group_content = re.sub(
                r'style="[^"]*?fill:[^;"]*',
                f'style="fill:{text_color}',
                group_content
            )
            # Change fill attribute
            group_content = re.sub(
                r'fill="#[0-9a-fA-F]{6}"',
                f'fill="{text_color}"',
                group_content
            )
            group_content = re.sub(
                r'fill="[^"]*"',
                f'fill="{text_color}"',
                group_content
            )
            return group_content

        result = re.sub(
            r'<g id="text_[^"]*"[^>]*>.*?</g>',
            replace_text_path_fill,
            result,
            flags=re.DOTALL
        )

        # 4. Circuit strokes (keep these as circuit color)
        result = re.sub(
            r'stroke:\s*#000000\b',
            f'stroke:{fg}',
            result
        )
        result = re.sub(
            r'stroke:\s*rgb\(0,\s*0,\s*0\)',
            f'stroke:{fg}',
            result
        )
        result = re.sub(
            r'stroke="\s*#000000\b"',
            f'stroke="{fg}"',
            result
        )
        result = re.sub(
            r'stroke="\s*black\b"',
            f'stroke="{fg}"',
            result
        )

        # 5. Component fills - only non-text elements
        # Skip elements that are part of text groups
        result = re.sub(
            r'(<(?!(?:text|tspan|g id="text_))[^>]*?)fill:\s*#000000\b',
            rf'\1fill:{fg}',
            result
        )
        result = re.sub(
            r'(<(?!(?:text|tspan|g id="text_))[^>]*?)fill:\s*rgb\(0,\s*0,\s*0\)',
            rf'\1fill:{fg}',
            result
        )
        result = re.sub(
            r'(<(?!(?:text|tspan|g id="text_))[^>]*?)fill="\s*#000000\b"',
            rf'\1fill="{fg}"',
            result
        )
        result = re.sub(
            r'(<(?!(?:text|tspan|g id="text_))[^>]*?)fill="\s*black\b"',
            rf'\1fill="{fg}"',
            result
        )

        # 6. Add background rectangle
        bg_rect = f'<rect width="100%" height="100%" fill="{bg}"/>'
        result = re.sub(r'(<svg[^>]*>)', r'\1' + bg_rect, result, count=1)

        return result


def _render_svg(code: str, out_path: str, text_color: str | None = None) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import schemdraw
    import schemdraw.elements as elm

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Keep text as actual text elements instead of paths
    plt.rcParams["svg.fonttype"] = "none"
    
    if text_color:
        plt.rcParams["text.color"] = text_color
        plt.rcParams["figure.facecolor"] = "none"
        plt.rcParams["axes.facecolor"] = "none"

    exec_code = code.replace(
        "with schemdraw.Drawing() as d:",
        f"with schemdraw.Drawing(file={str(out)!r}, show=False) as d:",
        1,
    )

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
    circuit = analyse_topology(elements)

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