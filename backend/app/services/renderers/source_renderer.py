from __future__ import annotations

from app.core.netlist_builder import CircuitBuilder


class SourceRenderer:
    @staticmethod
    def render(builder: CircuitBuilder, component: dict) -> None:
        comp_type = component.get("component_type", "")
        name_raw = component.get("name", "1")
        nodes = component.get("nodes", [])
        params = component.get("parameters", {})
        model = component.get("model")

        if comp_type == "voltage_source":
            name = name_raw.lstrip("V") or "1"
            dc_val = params.get("dc_value")
            ac_val = params.get("ac_value")
            ac_amp = params.get("ac_amplitude")
            pulse = params.get("pulse")
            sine = params.get("sine")
            pwl = params.get("pwl")
            builder.voltage_source(
                name,
                nodes[0],
                nodes[1],
                dc=float(dc_val) if dc_val is not None else None,
                ac=float(ac_val or ac_amp) if ac_val is not None or ac_amp is not None else None,
                pulse=pulse if pulse else None,
                sine=sine if sine else None,
                pwl=pwl if pwl else None,
            )
        elif comp_type == "current_source":
            name = name_raw.lstrip("I") or "1"
            dc_val = params.get("dc_value")
            ac_val = params.get("ac_value")
            builder.current_source(
                name,
                nodes[0],
                nodes[1],
                dc=float(dc_val) if dc_val is not None else None,
                ac=float(ac_val) if ac_val is not None else None,
            )

    @staticmethod
    def render_diode(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("D") or "1"
        nodes = component.get("nodes", [])
        model = component.get("model") or "DEFAULT"
        builder.diode(name, nodes[0], nodes[1], model)
