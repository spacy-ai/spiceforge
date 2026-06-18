from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from app.services.circuit_planner import OpenCodeClient


@dataclass
class ModifyResult:
    blueprint: dict
    changes_summary: str


def _diff_blueprints(old_bp: dict, new_bp: dict) -> str:
    old_components = {
        c.get("name", ""): c for c in old_bp.get("components", [])
    }
    new_components = {
        c.get("name", ""): c for c in new_bp.get("components", [])
    }

    old_names = set(old_components.keys())
    new_names = set(new_components.keys())

    added = new_names - old_names
    removed = old_names - new_names
    common = old_names & new_names

    lines: list[str] = []

    for name in sorted(added):
        comp = new_components[name]
        ctype = comp.get("component_type", "?")
        nodes = " -> ".join(comp.get("nodes", []))
        params = comp.get("parameters", {})
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        lines.append(f"Added: {name} ({ctype}, {nodes}) [{param_str}]")

    for name in sorted(removed):
        comp = old_components[name]
        ctype = comp.get("component_type", "?")
        lines.append(f"Removed: {name} ({ctype})")

    for name in sorted(common):
        old_params = old_components[name].get("parameters", {})
        new_params = new_components[name].get("parameters", {})
        for key in set(old_params.keys()) | set(new_params.keys()):
            old_val = old_params.get(key)
            new_val = new_params.get(key)
            if old_val != new_val:
                lines.append(f"Changed: {name}.{key} {old_val} → {new_val}")

    old_nodes_in = set(old_bp.get("input_nodes", []))
    new_nodes_in = set(new_bp.get("input_nodes", []))
    if old_nodes_in != new_nodes_in:
        lines.append(
            f"Changed: input_nodes {sorted(old_nodes_in)} → {sorted(new_nodes_in)}"
        )

    old_nodes_out = set(old_bp.get("output_nodes", []))
    new_nodes_out = set(new_bp.get("output_nodes", []))
    if old_nodes_out != new_nodes_out:
        lines.append(
            f"Changed: output_nodes {sorted(old_nodes_out)} → {sorted(new_nodes_out)}"
        )

    old_analyses = old_bp.get("analyses", [])
    new_analyses = new_bp.get("analyses", [])
    old_types = [a.get("type", "") for a in old_analyses]
    new_types = [a.get("type", "") for a in new_analyses]
    if old_types != new_types:
        lines.append(f"Changed: analyses {old_types} → {new_types}")

    if not lines:
        return "No structural changes detected (description/title may have updated)."

    return "\n".join(lines)


class ModifyService:
    def __init__(self, llm_client: Optional[OpenCodeClient] = None):
        self._llm = llm_client

    def modify(
        self,
        current_blueprint: dict,
        modification_request: str,
        current_netlist: str = "",
    ) -> Optional[ModifyResult]:
        if self._llm is None:
            return None

        system = (
            "You are a circuit modification planner. "
            "Given a current circuit blueprint and a modification request, "
            "produce an updated blueprint with ONLY the requested changes applied.\n\n"
            "RULES:\n"
            "- Only change what the user asks for. Preserve everything else.\n"
            "- Output a COMPLETE updated blueprint JSON.\n"
            "- Keep the same circuit_id.\n"
            "- Do NOT change analysis types unless requested.\n"
            "- Only output valid JSON, no explanation.\n\n"
            "Output must match the standard CircuitBlueprint schema."
        )

        prompt_data = {
            "current_blueprint": current_blueprint,
            "modification_request": modification_request,
            "current_netlist": current_netlist if current_netlist else None,
        }

        try:
            raw = self._llm.generate(
                system_prompt=system,
                user_prompt=json.dumps(prompt_data, indent=2),
                response_format="json",
                temperature=0.2,
                max_tokens=2000,
            )
            updated = json.loads(raw)
            changes = _diff_blueprints(current_blueprint, updated)
            return ModifyResult(blueprint=updated, changes_summary=changes)
        except Exception:
            return None


def modify_circuit(
    current_blueprint: dict,
    modification_request: str,
    current_netlist: str = "",
    llm_client: Optional[OpenCodeClient] = None,
) -> Optional[ModifyResult]:
    return ModifyService(llm_client=llm_client).modify(
        current_blueprint, modification_request, current_netlist
    )
