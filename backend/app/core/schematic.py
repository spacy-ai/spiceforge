from __future__ import annotations

import re
from dataclasses import dataclass, field

import schemdraw
import schemdraw.elements as elm


@dataclass
class ParsedComponent:
    comp_type: str
    ref: str
    nodes: list[str] = field(default_factory=list)
    value: str = ""


_COMPONENT_NODE_COUNTS: dict[str, int] = {
    "R": 2,
    "C": 2,
    "L": 2,
    "V": 2,
    "I": 2,
    "D": 2,
    "Q": 3,
    "J": 3,
    "M": 4,
    "E": 4,
    "G": 4,
    "F": 2,
    "H": 2,
    "B": 2,
}

_GROUND_NAMES = {"0", "gnd", "gnd!"}

_ELEMENT_MAP: dict[str, type] = {
    "R": elm.Resistor,
    "C": elm.Capacitor,
    "L": elm.Inductor,
    "V": elm.SourceV,
    "I": elm.SourceI,
    "D": elm.Diode,
    "Q": elm.BjtNpn,
    "M": elm.NFet,
    "X": elm.Opamp,
}


def _is_ground(node: str) -> bool:
    return node.lower() in _GROUND_NAMES


def parse_netlist_components(netlist: str) -> list[ParsedComponent]:
    components: list[ParsedComponent] = []

    for line in netlist.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("*"):
            continue
        if stripped.startswith("."):
            continue
        if stripped.startswith("+"):
            continue

        tokens = stripped.split()
        if not tokens:
            continue

        ref = tokens[0]
        comp_type = ref[0].upper()

        if comp_type == "X":
            if len(tokens) >= 3:
                nodes = [n.lower() for n in tokens[1:-1]]
                value = tokens[-1]
            else:
                nodes = []
                value = ""
        elif comp_type in _COMPONENT_NODE_COUNTS:
            n_nodes = _COMPONENT_NODE_COUNTS[comp_type]
            nodes = [n.lower() for n in tokens[1 : 1 + n_nodes]]
            value = " ".join(tokens[1 + n_nodes :])
        else:
            nodes = [n.lower() for n in tokens[1:3]] if len(tokens) >= 3 else []
            value = " ".join(tokens[3:]) if len(tokens) > 3 else ""

        components.append(
            ParsedComponent(
                comp_type=comp_type,
                ref=ref,
                nodes=nodes,
                value=value,
            )
        )

    return components


def _is_ac_source(comp: ParsedComponent) -> bool:
    return bool(re.search(r"\bac\b", comp.value, re.IGNORECASE))


def _classify_components(
    components: list[ParsedComponent],
) -> tuple[list[ParsedComponent], list[ParsedComponent], list[ParsedComponent]]:
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

    return sources, series, shunt


def _draw_sources(
    d: schemdraw.Drawing,
    sources: list[ParsedComponent],
    node_positions: dict[str, tuple[float, float]],
) -> None:
    for comp in sources:
        elem_cls = elm.SourceSin if _is_ac_source(comp) else _ELEMENT_MAP.get(comp.comp_type, elm.SourceV)
        e = d.add(elem_cls().up().label(comp.ref))
        if comp.nodes:
            node_positions[comp.nodes[0]] = e.end
            if len(comp.nodes) > 1:
                node_positions[comp.nodes[1]] = e.start


def _draw_series(
    d: schemdraw.Drawing,
    series: list[ParsedComponent],
    node_positions: dict[str, tuple[float, float]],
) -> None:
    for comp in series:
        elem_cls = _ELEMENT_MAP.get(comp.comp_type, elm.Resistor)
        e = d.add(elem_cls().right().label(comp.ref))
        if comp.nodes:
            node_positions[comp.nodes[0]] = e.start
            if len(comp.nodes) > 1:
                node_positions[comp.nodes[1]] = e.end


def _draw_shunt(
    d: schemdraw.Drawing,
    shunt: list[ParsedComponent],
    node_positions: dict[str, tuple[float, float]],
) -> None:
    for comp in shunt:
        elem_cls = _ELEMENT_MAP.get(comp.comp_type, elm.Resistor)
        signal_node = None
        for node in comp.nodes:
            if not _is_ground(node):
                signal_node = node
                break

        if signal_node and signal_node in node_positions:
            d.add(elm.Line().at(node_positions[signal_node]).down().length(0.5))

        d.add(elem_cls().down().label(comp.ref))
        d.add(elm.Ground())


def _draw_source_ground(
    d: schemdraw.Drawing,
    sources: list[ParsedComponent],
    node_positions: dict[str, tuple[float, float]],
) -> None:
    ground_pos = None
    for comp in sources:
        for node in comp.nodes:
            if _is_ground(node) and node in node_positions:
                ground_pos = node_positions[node]
                break
        if ground_pos is not None:
            break

    if ground_pos is not None:
        d.add(elm.Ground().at(ground_pos))


def render_schematic_svg(netlist: str) -> str:
    components = parse_netlist_components(netlist)
    if not components:
        raise ValueError("Netlist contains no components to draw")

    sources, series, shunt = _classify_components(components)

    drawing = schemdraw.Drawing(backend="svg", show=False)
    node_positions: dict[str, tuple[float, float]] = {}

    _draw_sources(drawing, sources, node_positions)
    _draw_series(drawing, series, node_positions)
    _draw_shunt(drawing, shunt, node_positions)
    _draw_source_ground(drawing, sources, node_positions)

    return drawing.get_imagedata("svg").decode("utf-8")
