from __future__ import annotations

import json
from typing import Optional

from app.services.circuit_planner import OpenCodeClient


class ModifyService:
    def __init__(self, llm_client: Optional[OpenCodeClient] = None):
        self._llm = llm_client

    def modify(
        self,
        current_blueprint: dict,
        modification_request: str,
        current_netlist: str = "",
    ) -> Optional[dict]:
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
            return json.loads(raw)
        except Exception:
            return None


def modify_circuit(
    current_blueprint: dict,
    modification_request: str,
    current_netlist: str = "",
    llm_client: Optional[OpenCodeClient] = None,
) -> Optional[dict]:
    return ModifyService(llm_client=llm_client).modify(
        current_blueprint, modification_request, current_netlist
    )
