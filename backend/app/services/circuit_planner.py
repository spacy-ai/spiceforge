from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional

import requests


@dataclass
class ComponentSpec:
    component_type: str
    name: str
    nodes: list[str]
    parameters: dict
    model: Optional[str] = None


@dataclass
class CircuitBlueprint:
    circuit_id: str
    description: str
    input_nodes: list[str]
    output_nodes: list[str]
    ground_node: str = "0"
    components: list[ComponentSpec] = field(default_factory=list)
    analyses: list[dict] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    topology_notes: str = ""
    design_decisions: list[str] = field(default_factory=list)
    summary: str = ""


class OpenCodeClient:
    DEFAULT_BASE = "https://opencode.ai/zen/v1"
    DEFAULT_MODEL = "minimax-m2.5-free"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 3000,
        timeout: int = 54,
    ):
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenCode API key is required. Set OPENCODE_API_KEY env var."
            )

        self.api_base = (
            api_base or os.environ.get("OPENCODE_API_BASE", self.DEFAULT_BASE)
        ).rstrip("/")
        self.model = model or os.environ.get("OPENCODE_MODEL", self.DEFAULT_MODEL)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    @staticmethod
    def _strip_json_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: str = "text",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        resp = self._session.post(
            f"{self.api_base}/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        if response_format == "json":
            content = self._strip_json_fences(content)

        return content


class Planner:
    SYSTEM_PROMPT = """You are the Planner in the SPACY circuit design system. Your role is to analyze natural language circuit descriptions and create detailed circuit blueprints.

STRICT OUTPUT RULES:
- Return ONLY a valid JSON object — no markdown, no explanation, no preamble.
- All node names must be consistent strings that comply with SPICE/LTspice conventions.
- Ground must always be node "0".

ADDITIONAL FIELD:
- "summary": A short, human-readable explanation of the circuit.
  - Must describe what the circuit does in plain English
  - Must mention the components and their purpose
  - Keep it concise (2-4 sentences)
  - Do NOT include SPICE syntax, node names, or JSON terminology
  - Must always be present in every response

REQUIRED PARAMETERS BY COMPONENT TYPE:
- resistor: {"resistance": <ohms>}
- capacitor: {"capacitance": <farads>}
- inductor: {"inductance": <henries>}
- voltage_source: {"dc_value": <volts>}
- current_source: {"dc_value": <amps>}
- diode: {"model": "<model_name>"}
- mosfet: {"w": <width>, "l": <length>, "model": "<model_name>"}
- bjt: {"model": "<model_name>"}
- opamp: {"model": "<model_name>"}

REQUIRED PARAMETERS BY ANALYSIS TYPE:
For each analysis type, include ALL required parameters:

- transient:
  {
    "type": "transient",
    "parameters": {
      "tstart": <float>,
      "tstop": <float>,
      "tstep": <float>
    }
  }

- ac:
  {
    "type": "ac",
    "parameters": {
      "start_freq": <float>,
      "stop_freq": <float>,
      "num_points": <int>
    }
  }

- dc:
  {
    "type": "dc",
    "parameters": {
      "source": <string>,
      "start": <float>,
      "stop": <float>,
      "step": <float>
    }
  }

- op:
  {
    "type": "op"
  }

- dc_sweep:
  {
    "type": "dc_sweep",
    "parameters": {
      "source": <string>,
      "start": <float>,
      "stop": <float>,
      "step": <float>
    }
  }

JSON SCHEMA:
{
  "circuit_id": "<short_snake_case_id>",
  "description": "<original description verbatim>",
  "input_nodes": ["Vin"],
  "output_nodes": ["Vout"],
  "ground_node": "0",
  "components": [
    {
      "component_type": "resistor|capacitor|inductor|mosfet|bjt|opamp|voltage_source|current_source|diode",
      "name": "R1",
      "nodes": ["node_a", "node_b"],
      "parameters": {"resistance": 10000},
      "model": null
    }
  ],
  "analyses": [
    {
      "type": "ac|dc|transient|op|dc_sweep",
      "parameters": {}
    }
  ],
  "constraints": {},
  "topology_notes": "<brief explanation of topology choices>",
  "design_decisions": ["<decision 1>", "<decision 2>"],
  "summary": "<concise human-readable explanation of the circuit>"
}"""

    @staticmethod
    def _apply_safety_fixes(blueprint: CircuitBlueprint) -> CircuitBlueprint:
        fixed_components = []
        for comp in blueprint.components:
            params = dict(comp.parameters)
            comp_type = comp.component_type.lower()
            if comp_type == "voltage_source" and "dc_value" not in params:
                params["dc_value"] = 5
            elif comp_type == "current_source" and "dc_value" not in params:
                params["dc_value"] = 1
            fixed_components.append(
                ComponentSpec(
                    component_type=comp.component_type,
                    name=comp.name,
                    nodes=list(comp.nodes),
                    parameters=params,
                    model=comp.model,
                )
            )

        fixed_analyses = []
        for analysis in blueprint.analyses:
            analysis = dict(analysis)
            atype = analysis.get("type", "").lower()
            if atype == "transient":
                params = analysis.setdefault("parameters", {})
                params.setdefault("tstart", 0)
                params.setdefault("tstop", 1e-3)
                params.setdefault("tstep", 1e-6)
            elif atype == "ac":
                params = analysis.setdefault("parameters", {})
                params.setdefault("start_freq", 1)
                params.setdefault("stop_freq", 1e6)
                params.setdefault("num_points", 100)
            elif atype == "dc" or atype == "dc_sweep":
                params = analysis.setdefault("parameters", {})
                params.setdefault("source", "V1")
                params.setdefault("start", 0)
                params.setdefault("stop", 1)
                params.setdefault("step", 0.1)
            fixed_analyses.append(analysis)

        return CircuitBlueprint(
            circuit_id=blueprint.circuit_id,
            description=blueprint.description,
            input_nodes=list(blueprint.input_nodes),
            output_nodes=list(blueprint.output_nodes),
            ground_node=blueprint.ground_node,
            components=fixed_components,
            analyses=fixed_analyses,
            constraints=dict(blueprint.constraints),
            topology_notes=blueprint.topology_notes,
            design_decisions=list(blueprint.design_decisions),
            summary=blueprint.summary,
        )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        self._client = OpenCodeClient(
            api_key=api_key,
            api_base=api_base,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def create_plan(self, description: str) -> CircuitBlueprint:
        prompt = (
            f"Analyze the following circuit description and return a complete JSON blueprint.\n\n"
            f"DESCRIPTION:\n{description}\n\n"
            f"Include every component with correct node connections, all required analyses, "
            f"design constraints, and brief reasoning for your topology choices."
        )

        raw = self._client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            response_format="json",
        )

        data = json.loads(raw)
        blueprint = CircuitBlueprint(
            circuit_id=data.get("circuit_id", "unnamed"),
            description=data.get("description", ""),
            input_nodes=data.get("input_nodes", []),
            output_nodes=data.get("output_nodes", []),
            ground_node=data.get("ground_node", "0"),
            components=[ComponentSpec(**c) for c in data.get("components", [])],
            analyses=data.get("analyses", []),
            constraints=data.get("constraints", {}),
            topology_notes=data.get("topology_notes", ""),
            design_decisions=data.get("design_decisions", []),
            summary=data.get("summary", ""),
        )
        return self._apply_safety_fixes(blueprint)
