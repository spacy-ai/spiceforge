from __future__ import annotations

from dataclasses import dataclass, field


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


def _is_ground(node: str) -> bool:
    return node.lower() in _GROUND_NAMES


def parse_netlist(netlist: str) -> list[ParsedComponent]:
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
