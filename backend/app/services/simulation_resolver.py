from __future__ import annotations

import json
from typing import Optional

from app.models.pipeline_models import ResolverResult, SimulationResult
from app.services.circuit_planner import OpenCodeClient


MAX_RETRIES = 2


class SimulationResolver:
    def __init__(self, llm_client: Optional[OpenCodeClient] = None):
        self._llm = llm_client

    def resolve(
        self,
        blueprint: dict,
        simulation_result: SimulationResult,
        previous_netlist: str = "",
        retry_count: int = 0,
    ) -> ResolverResult:
        if retry_count >= MAX_RETRIES:
            return ResolverResult(
                resolved=False,
                retry_count=retry_count,
                errors_remaining=["Max retries exceeded"],
            )

        if simulation_result.success:
            return ResolverResult(
                resolved=True,
                retry_count=retry_count,
            )

        if self._llm is None:
            return ResolverResult(
                resolved=False,
                retry_count=retry_count,
                errors_remaining=["No LLM available for resolver"],
            )

        return self._llm_resolve(blueprint, simulation_result, previous_netlist, retry_count)

    def _llm_resolve(
        self,
        blueprint: dict,
        sim_result: SimulationResult,
        netlist: str,
        retry_count: int,
    ) -> ResolverResult:
        diagnostics = []
        for d in sim_result.diagnostics:
            diagnostics.append(f"[{d.severity}] {d.category}: {d.message}")
        convergence = sim_result.convergence_failures or []

        prompt_data = {
            "blueprint": blueprint,
            "simulation_error": sim_result.error or "Unknown",
            "stdout": sim_result.stdout[-2000:] if sim_result.stdout else "",
            "stderr": sim_result.stderr[-2000:] if sim_result.stderr else "",
            "diagnostics": diagnostics,
            "convergence_failures": convergence,
            "netlist_snippet": netlist[-1000:] if netlist else "",
        }

        system = (
            "You are a simulation resolver for SPICE circuits. "
            "A simulation has failed. Analyze the errors and produce a minimal patch.\n\n"
            "RULES:\n"
            "- Prefer patching the blueprint (JSON).\n"
            "- Only patch the netlist directly as a last resort.\n"
            "- Make minimal changes to fix the specific failure.\n"
            "- Do NOT regenerate the entire circuit.\n"
            "- Only output valid JSON.\n\n"
            "Output schema:\n"
            "{\n"
            '  "patch_type": "blueprint" | "netlist",\n'
            '  "patched_blueprint": {...} | null,\n'
            '  "patched_netlist": "..." | null,\n'
            '  "patch_description": "brief explanation of what was changed and why",\n'
            '  "errors_remaining": ["..."]  // any issues that couldn\'t be resolved\n'
            "}"
        )

        try:
            raw = self._llm.generate(
                system_prompt=system,
                user_prompt=json.dumps(prompt_data, indent=2),
                response_format="json",
                temperature=0.2,
                max_tokens=1500,
            )
            data = json.loads(raw)
            return ResolverResult(
                resolved=len(data.get("errors_remaining", [])) == 0,
                patch_description=data.get("patch_description", ""),
                retry_count=retry_count + 1,
                patched_blueprint=data.get("patched_blueprint"),
                patched_netlist=data.get("patched_netlist"),
                errors_remaining=data.get("errors_remaining", []),
            )
        except Exception as exc:
            return ResolverResult(
                resolved=False,
                retry_count=retry_count + 1,
                errors_remaining=[f"Resolver error: {exc}"],
            )


def resolve_simulation(
    blueprint: dict,
    simulation_result: SimulationResult,
    previous_netlist: str = "",
    retry_count: int = 0,
    llm_client: Optional[OpenCodeClient] = None,
) -> ResolverResult:
    return SimulationResolver(llm_client=llm_client).resolve(
        blueprint, simulation_result, previous_netlist, retry_count
    )
