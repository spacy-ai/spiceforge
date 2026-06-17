from __future__ import annotations

from app.core.netlist_builder import CircuitBuilder
from app.models.pipeline_models import format_spice_value


class ResistorRenderer:
    @staticmethod
    def render(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("R") or "1"
        nodes = component.get("nodes", [])
        params = component.get("parameters", {})
        value = params.get("resistance", 1000)
        builder.resistor(name, nodes[0], nodes[1], format_spice_value(float(value)))


class CapacitorRenderer:
    @staticmethod
    def render(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("C") or "1"
        nodes = component.get("nodes", [])
        params = component.get("parameters", {})
        value = params.get("capacitance", 1e-6)
        builder.capacitor(name, nodes[0], nodes[1], format_spice_value(float(value)))


class InductorRenderer:
    @staticmethod
    def render(builder: CircuitBuilder, component: dict) -> None:
        name = component.get("name", "1").lstrip("L") or "1"
        nodes = component.get("nodes", [])
        params = component.get("parameters", {})
        value = params.get("inductance", 1e-3)
        builder.inductor(name, nodes[0], nodes[1], format_spice_value(float(value)))
