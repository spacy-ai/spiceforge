from __future__ import annotations

import json
from typing import Optional

from app.services.circuit_planner import OpenCodeClient


class ExplainService:
    def __init__(self, llm_client: Optional[OpenCodeClient] = None):
        self._llm = llm_client

    def explain(self, blueprint: dict, netlist: str) -> str:
        if self._llm is None:
            return self._explain_deterministic(blueprint, netlist)

        return self._llm_explain(blueprint, netlist)

    def _explain_deterministic(self, blueprint: dict, netlist: str) -> str:
        title = blueprint.get("title", "Circuit")
        desc = blueprint.get("description", "")
        components = blueprint.get("components", [])
        analyses = blueprint.get("analyses", [])

        lines = [f"# {title}", ""]
        if desc:
            lines.append(f"Description: {desc}")
            lines.append("")

        lines.append(f"Total components: {len(components)}")
        for comp in components:
            ctype = comp.get("component_type", "?")
            name = comp.get("name", "?")
            nodes = " -> ".join(comp.get("nodes", []))
            params = comp.get("parameters", {})
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            lines.append(f"  {name}: {ctype} ({nodes}) [{param_str}]")

        if analyses:
            lines.append("")
            lines.append(f"Analyses: {len(analyses)}")
            for a in analyses:
                atype = a.get("type", "?")
                params = a.get("parameters", {})
                param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                lines.append(f"  {atype}: {param_str}")

        return "\n".join(lines)

    def _llm_explain(self, blueprint: dict, netlist: str) -> str:
        system = (
            "You are a circuit explainer. Given a circuit blueprint and netlist, "
            "provide a clear, concise explanation of what the circuit does, "
            "how it works, and the role of each component.\n"
            "Format in plain English. 2-5 paragraphs."
        )
        prompt = json.dumps({"blueprint": blueprint, "netlist": netlist}, indent=2)

        try:
            return self._llm.generate(
                system_prompt=system,
                user_prompt=prompt,
                response_format="text",
                temperature=0.3,
                max_tokens=1000,
            ).strip()
        except Exception:
            return self._explain_deterministic(blueprint, netlist)


def explain_circuit(
    blueprint: dict,
    netlist: str,
    llm_client: Optional[OpenCodeClient] = None,
) -> str:
    return ExplainService(llm_client=llm_client).explain(blueprint, netlist)
