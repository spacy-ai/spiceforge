from __future__ import annotations

from app.core.netlist_builder import CircuitBuilder


class TransistorRenderer:
    @staticmethod
    def render_mosfet(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("M") or "1"
        nodes = component.get("nodes", [])
        params = component.get("parameters", {})
        model = component.get("model") or params.get("model", "NMOS")

        w = params.get("w")
        l = params.get("l")
        builder.mosfet(
            name,
            nodes[0], nodes[1], nodes[2], nodes[3] if len(nodes) > 3 else nodes[2],
            model,
            w=float(w) if w is not None else None,
            l=float(l) if l is not None else None,
        )

    @staticmethod
    def render_bjt(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("Q") or "1"
        nodes = component.get("nodes", [])
        model = component.get("model") or "NPN"
        area = component.get("parameters", {}).get("area")
        builder.bjt(
            name,
            nodes[0], nodes[1], nodes[2],
            model,
            area=float(area) if area is not None else None,
        )
