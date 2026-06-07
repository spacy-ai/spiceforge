from __future__ import annotations

import time
from typing import Optional

from app.core.netlist_builder import CircuitBuilder
from app.models.pipeline_models import SynthesisResult, format_spice_value
from app.services.renderers import (
    ResistorRenderer,
    CapacitorRenderer,
    SourceRenderer,
    TransistorRenderer,
    AnalysisRenderer,
)
from app.services.renderers.opamp_renderer import OpAmpRenderer
from app.services.renderers.resistor_renderer import InductorRenderer


_RENDERER_MAP = {
    "resistor": ("passive", ResistorRenderer.render),
    "capacitor": ("passive", CapacitorRenderer.render),
    "inductor": ("passive", InductorRenderer.render),
    "voltage_source": ("source", SourceRenderer.render),
    "current_source": ("source", SourceRenderer.render),
    "diode": ("diode", SourceRenderer.render_diode),
    "mosfet": ("transistor", TransistorRenderer.render_mosfet),
    "bjt": ("transistor", TransistorRenderer.render_bjt),
    "opamp": ("opamp", OpAmpRenderer.render),
}


class DeterministicSynthesizer:
    def synthesize(self, blueprint: dict) -> SynthesisResult:
        start = time.perf_counter()
        builder = CircuitBuilder()

        title = blueprint.get("title", "SPICY Circuit")
        builder.title(title)

        description = blueprint.get("description", "")
        if description:
            builder.comment(description)

        components = blueprint.get("components", [])
        for comp in components:
            self._render_component(builder, comp)

        analyses = blueprint.get("analyses", [])
        for analysis in analyses:
            AnalysisRenderer.render(builder, analysis)

        netlist = builder.netlist()
        elapsed = (time.perf_counter() - start) * 1000

        return SynthesisResult(
            netlist=netlist,
            synthesis_time_ms=elapsed,
            component_count=len(components),
        )

    def synthesize_with_models(self, blueprint: dict) -> SynthesisResult:
        builder = CircuitBuilder()

        title = blueprint.get("title", "SPICY Circuit")
        builder.title(title)

        description = blueprint.get("description", "")
        if description:
            builder.comment(description)

        components = blueprint.get("components", [])
        seen_models: set[str] = set()

        for comp in components:
            comp_type = comp.get("component_type", "").lower()
            model = comp.get("model")
            params = comp.get("parameters", {})

            if model and model not in seen_models:
                model_type = self._infer_model_type(comp_type, params)
                if model_type:
                    builder.model(model, model_type)
                    seen_models.add(model)

            self._render_component(builder, comp)

        analyses = blueprint.get("analyses", [])
        for analysis in analyses:
            AnalysisRenderer.render(builder, analysis)

        netlist = builder.netlist()
        return SynthesisResult(
            netlist=netlist,
            synthesis_time_ms=0.0,
            component_count=len(components),
        )

    @staticmethod
    def _render_component(builder: CircuitBuilder, comp: dict) -> None:
        comp_type = comp.get("component_type", "").lower()
        renderer_info = _RENDERER_MAP.get(comp_type)
        if renderer_info is None:
            return
        _, render_fn = renderer_info
        render_fn(builder, comp)

    @staticmethod
    def _infer_model_type(comp_type: str, params: dict) -> Optional[str]:
        if comp_type == "mosfet":
            return "NMOS"
        if comp_type == "bjt":
            return "NPN"
        if comp_type == "diode":
            return "D"
        return None


def deterministic_synthesize(blueprint: dict) -> SynthesisResult:
    return DeterministicSynthesizer().synthesize(blueprint)
