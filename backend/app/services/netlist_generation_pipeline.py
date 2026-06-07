from __future__ import annotations

from typing import Any, Optional

from app.core.blueprint_validator import (
    validate_circuit_blueprint,
    ValidationResult,
)
from app.models.pipeline_models import (
    ClarificationResult,
    IntentResult,
    IntentType,
    PipelineResult,
    ResolverResult,
    SimulationResult,
    SynthesisResult,
)
from app.services.blueprint_normalizer import normalize_blueprint
from app.services.circuit_planner import OpenCodeClient, Planner
from app.services.clarification_engine import ClarificationEngine
from app.services.deterministic_synthesizer import DeterministicSynthesizer
from app.services.explain_service import ExplainService
from app.services.intent_classifier import IntentClassifier
from app.services.modify_service import ModifyService
from app.services.simulation_resolver import SimulationResolver


class NetlistGenerationPipeline:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        planner_temperature: float = 0.3,
        synthesizer_llm: Optional[OpenCodeClient] = None,
    ):
        self._api_key = api_key
        self._api_base = api_base
        self._model = model
        self._planner_temperature = planner_temperature

        self._llm_client = OpenCodeClient(
            api_key=api_key,
            api_base=api_base,
            model=model,
            temperature=planner_temperature,
        ) if (api_key or model) else None

        self._planner = None  # lazy init
        self._intent_classifier = IntentClassifier(llm_client=self._llm_client)
        self._clarification_engine = ClarificationEngine(llm_client=self._llm_client)
        self._synthesizer = DeterministicSynthesizer()
        self._simulation = None  # lazy init
        self._resolver = SimulationResolver(llm_client=self._llm_client)
        self._explainer = ExplainService(llm_client=self._llm_client)
        self._modifier = ModifyService(llm_client=self._llm_client)
        self._planner = None  # lazy init

    def _get_planner(self) -> Planner:
        if self._planner is None:
            self._planner = Planner(
                api_key=self._api_key,
                api_base=self._api_base,
                model=self._model,
                temperature=self._planner_temperature,
            )
        return self._planner

    def run(
        self,
        prompt: str,
        existing_blueprint: Optional[dict] = None,
        run_simulation: bool = True,
        enable_resolver: bool = True,
        max_resolver_retries: int = 2,
        simulation_timeout: int = 30,
    ) -> PipelineResult:
        intent = self._intent_classifier.classify(prompt)

        if intent.intent == IntentType.EXPLAIN_CIRCUIT:
            return self._handle_explain(prompt, intent, existing_blueprint)

        if intent.intent == IntentType.MODIFY_CIRCUIT:
            return self._handle_modify(prompt, intent, existing_blueprint)

        return self._handle_create(
            prompt=prompt,
            intent=intent,
            run_simulation=run_simulation,
            enable_resolver=enable_resolver,
            max_resolver_retries=max_resolver_retries,
            simulation_timeout=simulation_timeout,
        )

    def _handle_create(
        self,
        prompt: str,
        intent: IntentResult,
        run_simulation: bool,
        enable_resolver: bool,
        max_resolver_retries: int,
        simulation_timeout: int,
    ) -> PipelineResult:
        clarification = self._clarification_engine.analyze(prompt)
        if clarification.needs_clarification:
            return PipelineResult(
                success=False,
                intent=intent,
                clarifications=clarification.questions,
                error="Additional information required",
            )

        try:
            planner = self._get_planner()
            blueprint = planner.create_plan_strict(prompt)
        except Exception as exc:
            return PipelineResult(
                success=False,
                intent=intent,
                error=f"Planning failed: {exc}",
            )

        blueprint_dict = {
            "circuit_id": blueprint.circuit_id,
            "title": blueprint.title,
            "description": blueprint.description,
            "input_nodes": blueprint.input_nodes,
            "output_nodes": blueprint.output_nodes,
            "ground_node": blueprint.ground_node,
            "components": [
                {
                    "component_type": c.component_type,
                    "name": c.name,
                    "nodes": c.nodes,
                    "parameters": c.parameters,
                    "model": c.model,
                }
                for c in blueprint.components
            ],
            "analyses": blueprint.analyses,
            "constraints": blueprint.constraints,
            "topology_notes": blueprint.topology_notes,
            "design_decisions": blueprint.design_decisions,
            "summary": blueprint.summary,
        }

        validation = self._validate(blueprint_dict)
        if not validation.is_valid:
            return PipelineResult(
                success=False,
                intent=intent,
                blueprint=blueprint_dict,
                validation=validation,
                error="Blueprint validation failed",
            )

        normalized = normalize_blueprint(blueprint_dict)
        synthesis = self._synthesize(normalized)
        if not synthesis.netlist:
            return PipelineResult(
                success=False,
                intent=intent,
                blueprint=normalized,
                validation=validation,
                error="Synthesis produced no netlist",
            )

        pipeline_result = PipelineResult(
            success=True,
            intent=intent,
            blueprint=normalized,
            validation=validation,
            synthesis=synthesis,
            title=blueprint.title or "",
            summary=blueprint.summary or "",
        )

        if run_simulation:
            sim_result = self._simulate(synthesis.netlist, simulation_timeout)
            pipeline_result.simulation = sim_result

            if not sim_result.success and enable_resolver:
                pipeline_result = self._resolve(
                    pipeline_result,
                    normalized,
                    synthesis.netlist,
                    max_resolver_retries,
                    simulation_timeout,
                )

        return pipeline_result

    def _handle_explain(
        self,
        prompt: str,
        intent: IntentResult,
        existing_blueprint: Optional[dict],
    ) -> PipelineResult:
        if existing_blueprint:
            explanation = self._explainer.explain(existing_blueprint, "")
            return PipelineResult(
                success=True,
                intent=intent,
                blueprint=existing_blueprint,
                summary=explanation,
            )

        try:
            planner = self._get_planner()
            blueprint = planner.create_plan_strict(prompt)
            blueprint_dict = {
                "circuit_id": blueprint.circuit_id,
                "title": blueprint.title,
                "description": blueprint.description,
                "input_nodes": blueprint.input_nodes,
                "output_nodes": blueprint.output_nodes,
                "ground_node": blueprint.ground_node,
                "components": [
                    {
                        "component_type": c.component_type,
                        "name": c.name,
                        "nodes": c.nodes,
                        "parameters": c.parameters,
                        "model": c.model,
                    }
                    for c in blueprint.components
                ],
                "analyses": blueprint.analyses,
                "constraints": blueprint.constraints,
                "topology_notes": blueprint.topology_notes,
                "design_decisions": blueprint.design_decisions,
                "summary": blueprint.summary,
            }
            normalized = normalize_blueprint(blueprint_dict)
            netlist = self._synthesizer.synthesize(normalized).netlist
            explanation = self._explainer.explain(normalized, netlist)
            return PipelineResult(
                success=True,
                intent=intent,
                blueprint=normalized,
                synthesis=SynthesisResult(netlist=netlist),
                summary=explanation,
                title=blueprint.title,
            )
        except Exception as exc:
            return PipelineResult(
                success=False,
                intent=intent,
                error=f"Explanation failed: {exc}",
            )

    def _handle_modify(
        self,
        prompt: str,
        intent: IntentResult,
        existing_blueprint: Optional[dict],
    ) -> PipelineResult:
        if not existing_blueprint:
            return PipelineResult(
                success=False,
                intent=intent,
                error="No existing blueprint to modify. Create a circuit first.",
            )

        try:
            updated = self._modifier.modify(existing_blueprint, prompt)
            if not updated:
                return PipelineResult(
                    success=False,
                    intent=intent,
                    blueprint=existing_blueprint,
                    error="Modification failed",
                )

            validation = self._validate(updated)
            if not validation.is_valid:
                return PipelineResult(
                    success=False,
                    intent=intent,
                    blueprint=updated,
                    validation=validation,
                    error="Modified blueprint validation failed",
                )

            normalized = normalize_blueprint(updated)
            synthesis = self._synthesize(normalized)
            return PipelineResult(
                success=True,
                intent=intent,
                blueprint=normalized,
                validation=validation,
                synthesis=synthesis,
                title=normalized.get("title", ""),
                summary=normalized.get("summary", ""),
            )
        except Exception as exc:
            return PipelineResult(
                success=False,
                intent=intent,
                blueprint=existing_blueprint,
                error=f"Modification failed: {exc}",
            )

    def _validate(self, blueprint: dict) -> ValidationResult:
        return validate_circuit_blueprint(blueprint)

    def _synthesize(self, blueprint: dict) -> SynthesisResult:
        return self._synthesizer.synthesize(blueprint)

    def _simulate(self, netlist: str, timeout: int) -> SimulationResult:
        if self._simulation is None:
            from app.services.simulation_stage import SimulationStage
            self._simulation = SimulationStage()
        return self._simulation.run(netlist, timeout)

    def _resolve(
        self,
        result: PipelineResult,
        blueprint: dict,
        netlist: str,
        max_retries: int,
        sim_timeout: int,
    ) -> PipelineResult:
        for attempt in range(max_retries):
            resolver_result = self._resolver.resolve(
                blueprint=blueprint,
                simulation_result=result.simulation,
                previous_netlist=netlist,
                retry_count=attempt,
            )
            result.resolution = resolver_result

            if resolver_result.resolved:
                break

            if resolver_result.patched_blueprint:
                val = self._validate(resolver_result.patched_blueprint)
                if not val.is_valid:
                    result.error = "Resolver patch failed validation"
                    break

                norm = normalize_blueprint(resolver_result.patched_blueprint)
                syn = self._synthesize(norm)
                if not syn.netlist:
                    result.error = "Resolver re-synthesis failed"
                    break

                result.blueprint = norm
                result.synthesis = syn
                netlist = syn.netlist

                sim = self._simulate(netlist, sim_timeout)
                result.simulation = sim

                if sim.success:
                    result.resolution.resolved = True
                    break
            elif resolver_result.patched_netlist:
                sim = self._simulate(resolver_result.patched_netlist, sim_timeout)
                result.simulation = sim
                if sim.success:
                    result.resolution.resolved = True
                    break

        if result.simulation and not result.simulation.success:
            result.success = False
            result.error = (
                result.error or "Simulation failed after all resolver retries"
            )

        return result


def run_pipeline(
    prompt: str,
    existing_blueprint: Optional[dict] = None,
    run_simulation: bool = True,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> PipelineResult:
    pipeline = NetlistGenerationPipeline(
        api_key=api_key, api_base=api_base, model=model
    )
    return pipeline.run(prompt, existing_blueprint, run_simulation)
