from __future__ import annotations

from collections import defaultdict

from app.core.kicad_export.parser import ParsedComponent, _is_ground
from app.core.kicad_export.types import KiCadSymbolInfo, PlacedComponent, Wire, _GRID
from app.core.kicad_export.symbols import resolve_symbol_info

_COL_SOURCES = 50.8
_COL_SERIES = 101.6
_COL_SHUNT = 152.4
_Y_START = 50.8
_Y_SPACING = 15.24


def snap_to_grid(val: float) -> float:
    return round(val / _GRID) * _GRID


def layout_components(components: list[ParsedComponent]) -> list[PlacedComponent]:
    sources: list[ParsedComponent] = []
    series: list[ParsedComponent] = []
    shunt: list[ParsedComponent] = []

    for comp in components:
        if comp.comp_type in ("V", "I"):
            sources.append(comp)
        elif any(_is_ground(n) for n in comp.nodes):
            shunt.append(comp)
        else:
            series.append(comp)

    placed: list[PlacedComponent] = []

    for i, comp in enumerate(sources):
        sym = resolve_symbol_info(comp.comp_type, comp.value)
        y = snap_to_grid(_Y_START + i * _Y_SPACING)
        placed.append(PlacedComponent(comp, _COL_SOURCES, y, 0, sym))

    for i, comp in enumerate(series):
        sym = resolve_symbol_info(comp.comp_type, comp.value)
        y = snap_to_grid(_Y_START + i * _Y_SPACING)
        placed.append(PlacedComponent(comp, _COL_SERIES, y, 270, sym))

    for i, comp in enumerate(shunt):
        sym = resolve_symbol_info(comp.comp_type, comp.value)
        y = snap_to_grid(_Y_START + i * _Y_SPACING)
        placed.append(PlacedComponent(comp, _COL_SHUNT, y, 0, sym))

    return placed


def pin_positions(placed: PlacedComponent) -> list[tuple[float, float]]:
    import math

    angle_rad = math.radians(placed.rotation)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    positions: list[tuple[float, float]] = []
    n_pins = min(len(placed.component.nodes), len(placed.symbol_info.pin_offsets))
    for i in range(n_pins):
        dx, dy = placed.symbol_info.pin_offsets[i]
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        positions.append((snap_to_grid(placed.x + rx), snap_to_grid(placed.y + ry)))

    return positions


def route_wires(
    placed_components: list[PlacedComponent],
) -> tuple[list[Wire], list[tuple[float, float]]]:
    net_pins: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for pc in placed_components:
        pins = pin_positions(pc)
        for idx, node in enumerate(pc.component.nodes):
            if idx < len(pins) and not _is_ground(node):
                net_pins[node].append(pins[idx])

    wires: list[Wire] = []
    junctions: list[tuple[float, float]] = []

    for _net, pin_list in net_pins.items():
        if len(pin_list) < 2:
            continue
        pin_list.sort()
        for i in range(len(pin_list) - 1):
            x1, y1 = pin_list[i]
            x2, y2 = pin_list[i + 1]
            if x1 != x2 and y1 != y2:
                mid = (snap_to_grid(x2), snap_to_grid(y1))
                wires.append(Wire((x1, y1), mid))
                wires.append(Wire(mid, (x2, y2)))
                if i > 0:
                    junctions.append((x1, y1))
            else:
                wires.append(Wire((x1, y1), (x2, y2)))
                if i > 0:
                    junctions.append((x1, y1))

        if len(pin_list) > 2:
            junctions.append(pin_list[1])

    return wires, junctions


def find_ground_pins(
    placed_components: list[PlacedComponent],
) -> list[tuple[float, float]]:
    ground_positions: list[tuple[float, float]] = []
    for pc in placed_components:
        pins = pin_positions(pc)
        for idx, node in enumerate(pc.component.nodes):
            if idx < len(pins) and _is_ground(node):
                ground_positions.append(pins[idx])
    return ground_positions


def find_net_labels(
    placed_components: list[PlacedComponent],
) -> list[tuple[float, float, str]]:
    net_pins: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for pc in placed_components:
        pins = pin_positions(pc)
        for idx, node in enumerate(pc.component.nodes):
            if idx < len(pins) and not _is_ground(node):
                net_pins[node].append(pins[idx])

    labels: list[tuple[float, float, str]] = []
    for net_name, pin_list in net_pins.items():
        if net_name.isdigit():
            continue
        if pin_list:
            x, y = pin_list[0]
            labels.append((x, y, net_name))

    return labels
