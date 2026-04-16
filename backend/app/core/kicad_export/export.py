from __future__ import annotations

from pathlib import Path

from app.core.kicad_export.emitters import (
    emit_header,
    emit_junction,
    emit_net_label,
    emit_power_symbol,
    emit_sheet_instances,
    emit_symbol_instance,
    emit_wire,
)
from app.core.kicad_export.layout import (
    find_ground_pins,
    find_net_labels,
    layout_components,
    route_wires,
)
from app.core.kicad_export.parser import parse_netlist
from app.core.kicad_export.symbols import GND_LIB_SYMBOL, build_lib_symbols
from app.core.sanitize import validate_filename


def export_kicad_schematic(
    netlist: str,
    output_dir: Path | None = None,
    filename: str = "circuit.kicad_sch",
) -> tuple[Path, list[str]]:
    validate_filename(filename)

    components = parse_netlist(netlist)
    if not components:
        raise ValueError("Netlist contains no components to export")

    warnings: list[str] = []

    for comp in components:
        if comp.comp_type == "M" and len(comp.nodes) == 4:
            bulk = comp.nodes[3]
            source = comp.nodes[2]
            if bulk.lower() != source.lower():
                warnings.append(
                    f"{comp.ref}: bulk node '{bulk}' differs from source "
                    f"'{source}'; bulk connection dropped in KiCad export"
                )
            comp.nodes = comp.nodes[:3]

    sheet_uuid = __import__("uuid").uuid4().hex

    placed = layout_components(components)
    wires, junctions = route_wires(placed)
    ground_positions = find_ground_pins(placed)
    net_labels = find_net_labels(placed)

    used_lib_ids: set[str] = set()
    for pc in placed:
        used_lib_ids.add(pc.symbol_info.lib_id)

    parts: list[str] = []
    parts.append(emit_header(sheet_uuid))

    lib_sym = build_lib_symbols(used_lib_ids)
    if ground_positions:
        lib_sym = lib_sym.replace("  )", GND_LIB_SYMBOL + "\n  )", 1)
    parts.append(lib_sym)
    parts.append("")

    for pc in placed:
        parts.append(emit_symbol_instance(pc, sheet_uuid))
        parts.append("")

    for wire in wires:
        parts.append(emit_wire(wire))

    for jx, jy in junctions:
        parts.append(emit_junction(jx, jy))

    for gx, gy in ground_positions:
        parts.append(emit_power_symbol(gx, gy, sheet_uuid))
        parts.append("")

    for lx, ly, name in net_labels:
        parts.append(emit_net_label(lx, ly, name))

    parts.append(emit_sheet_instances(sheet_uuid))
    parts.append(")")

    output_dir = output_dir or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text("\n".join(parts), encoding="utf-8")
    return output_path, warnings
