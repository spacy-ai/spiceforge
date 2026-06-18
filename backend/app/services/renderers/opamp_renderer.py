from __future__ import annotations

from app.core.netlist_builder import CircuitBuilder


class OpAmpRenderer:
    @staticmethod
    def render(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("U") or "1"
        nodes = component.get("nodes", [])

        # Core nodes: [output, inverting_input, non_inverting_input]
        nout = nodes[0] if len(nodes) > 0 else "Vout"
        ninv = nodes[1] if len(nodes) > 1 else "ninv"
        nnoninv = nodes[2] if len(nodes) > 2 else "nnoninv"

        builder.opamp(name, nout, ninv, nnoninv)
