from __future__ import annotations

import uuid

from app.core.kicad_export.types import PlacedComponent, Wire


def _uid() -> str:
    return str(uuid.uuid4())


def emit_header(sheet_uuid: str) -> str:
    return f"""\
(kicad_sch
  (version 20231120)
  (generator "spice-platform")
  (generator_version "0.1")
  (uuid "{sheet_uuid}")
  (paper "A4")
"""


def emit_symbol_instance(placed: PlacedComponent, sheet_uuid: str) -> str:
    comp = placed.component
    sym = placed.symbol_info
    sym_uuid = _uid()

    pin_lines: list[str] = []
    n_pins = min(len(comp.nodes), len(sym.pin_numbers))
    for i in range(n_pins):
        pin_lines.append(f'        (pin "{sym.pin_numbers[i]}" (uuid "{_uid()}"))')

    angle = placed.rotation

    props = [
        f'      (property "Reference" "{comp.ref}" (at {placed.x + 2.54} {placed.y} 0)'
        f"\n        (effects (font (size 1.27 1.27))))",
        f'      (property "Value" "{comp.value}" (at {placed.x + 2.54} {placed.y + 2.54} 0)'
        f"\n        (effects (font (size 1.27 1.27))))",
        f'      (property "Footprint" "" (at {placed.x} {placed.y} 0)'
        f"\n        (effects (font (size 1.27 1.27)) hide))",
        f'      (property "Datasheet" "~" (at {placed.x} {placed.y} 0)'
        f"\n        (effects (font (size 1.27 1.27)) hide))",
    ]

    lines = [
        f'    (symbol (lib_id "{sym.lib_id}") (at {placed.x} {placed.y} {angle})',
        f'      (uuid "{sym_uuid}")',
    ]
    lines.extend(props)
    lines.append("      (pin_names (offset 1.016))")
    lines.append("      (instances")
    lines.append('        (project ""')
    lines.append(f'          (path "/{sheet_uuid}"')
    lines.append(f'            (reference "{comp.ref}") (unit 1)')
    lines.append("          )")
    lines.append("        )")
    lines.append("      )")
    if pin_lines:
        lines.extend(pin_lines)
    lines.append("    )")
    return "\n".join(lines)


def emit_wire(wire: Wire) -> str:
    x1, y1 = wire.start
    x2, y2 = wire.end
    return (
        f"    (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))\n"
        f"      (stroke (width 0) (type default))\n"
        f'      (uuid "{_uid()}")\n'
        f"    )"
    )


def emit_power_symbol(x: float, y: float, sheet_uuid: str) -> str:
    sym_uuid = _uid()
    return (
        f'    (symbol (lib_id "power:GND") (at {x} {y + 2.54} 0)\n'
        f"      (mirror y)\n"
        f'      (uuid "{sym_uuid}")\n'
        f'      (property "Reference" "#PWR?" (at {x} {y + 3.81} 0)\n'
        f"        (effects (font (size 1.27 1.27)) hide))\n"
        f'      (property "Value" "GND" (at {x} {y + 5.08} 0)\n'
        f"        (effects (font (size 1.27 1.27)) hide))\n"
        f'      (property "Footprint" "" (at {x} {y} 0)\n'
        f"        (effects (font (size 1.27 1.27)) hide))\n"
        f'      (property "Datasheet" "" (at {x} {y} 0)\n'
        f"        (effects (font (size 1.27 1.27)) hide))\n"
        f"      (pin_names (offset 0))\n"
        f"      (instances\n"
        f'        (project ""\n'
        f'          (path "/{sheet_uuid}"\n'
        f'            (reference "#PWR?") (unit 1)\n'
        f"          )\n"
        f"        )\n"
        f"      )\n"
        f'      (pin "1" (uuid "{_uid()}"))\n'
        f"    )"
    )


def emit_junction(x: float, y: float) -> str:
    return (
        f"    (junction (at {x} {y}) (diameter 0) (color 0 0 0 0)\n"
        f'      (uuid "{_uid()}")\n'
        f"    )"
    )


def emit_net_label(x: float, y: float, name: str) -> str:
    return (
        f'    (label "{name}" (at {x} {y - 2.54} 0) (fields_autoplaced yes)\n'
        f"      (effects (font (size 1.27 1.27)))\n"
        f'      (uuid "{_uid()}")\n'
        f"    )"
    )


def emit_sheet_instances(sheet_uuid: str) -> str:
    return (
        f'  (sheet_instances\n    (path "/{sheet_uuid}"\n      (page "1")\n    )\n  )'
    )
