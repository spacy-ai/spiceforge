from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
import requests

load_dotenv()  # Load environment variables from .env file


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
    title: str = ""
    input_nodes: list[str] = field(default_factory=list)
    output_nodes: list[str] = field(default_factory=list)
    ground_node: str = "0"
    components: list[ComponentSpec] = field(default_factory=list)
    analyses: list[dict] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    topology_notes: str = ""
    design_decisions: list[str] = field(default_factory=list)
    summary: str = ""


class OpenCodeClient:
      

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 100000,
        timeout: int = 12000,
    ):
        self.api_key = os.getenv("OPENCODE_API_KEY") if api_key is None else api_key
        if not self.api_key:
            raise ValueError(
                "OpenCode API key is required. Set OPENCODE_API_KEY env var."
            )

        self.api_base = (
            api_base or os.getenv("OPENCODE_API_BASE")
        ).rstrip("/")
        self.model = model or os.getenv("OPENCODE_MODEL")
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

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        resp = self._session.post(
            f"{self.api_base}",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(f"OpenCode error: {data['error']}")

        choice = (data.get("choices") or [{}])[0]
        content = (
            choice.get("message", {}).get("content")
            or choice.get("text")
            or ""
        )

        if not content:
            raise ValueError(f"OpenCode returned empty content: {data}")

        if response_format == "json":
            content = self._strip_json_fences(content)

        return content


class Planner:
    SYSTEM_PROMPT = """You are the Planner in the SPACY circuit design system. Convert a natural language circuit description into a validated JSON blueprint.
###
ABSOLUTE OUTPUT RULE:
Output MUST be a single valid JSON object. Start with { and end with }. No markdown, no explanation, no preamble, no trailing text. Must pass json.loads() with zero modification.
###
JSON RULES:
- No trailing commas
- No comments
- All strings properly escaped
- All brackets closed
- Ground node is always "0"
###
MANDATORY FIELDS — ANY MISSING FIELD = INVALID RESPONSE:
- "title"    → non-empty string
- "summary"  → non-empty string, exactly 2-4 sentences
- "analyses" → array with at least one analysis object
###
FIELD RULES:
TITLE:
- 3-8 words reflecting actual circuit type (filter, amplifier, oscillator, rectifier)
- No raw prompt copying, no leading/trailing whitespace
- Good: "RC Low Pass Filter" | "Common Emitter Amplifier"
- Bad:  "make a circuit with 1k and 1uF" | "circuit"
SUMMARY:
- 2-4 sentences, plain English
- Must explain: (1) what the circuit does, (2) key components and their roles, (3) overall behavior
- Must NOT contain: SPICE syntax, node names (Vin/Vout/n1), JSON field names
- Good: "This is an RC low-pass filter that attenuates high-frequency signals. It uses a resistor and capacitor to form a frequency-dependent voltage divider. The cutoff frequency is approximately 159 Hz."
- Bad:  "R1 connects Vin to Vout. The analyses array contains ac."
COMPONENT NAMES:
- Standard prefixed identifiers only: R1, C1, L1, V1, I1, D1, M1, Q1, U1
- Number sequentially per type: R1, R2, R3 (never R1, R3, R7)
- Nodes shared between components must use identical strings
COMPONENT PARAMETERS BY TYPE:
- resistor:       { "resistance": <number> }           — ONLY numeric, e.g. 10000, never "10k" or "10000 ohms"
- capacitor:      { "capacitance": <number> }          — ONLY numeric in farads, e.g. 1e-6
- inductor:       { "inductance": <number> }           — ONLY numeric in henries
- voltage_source: { "dc_value": <number> }             — ONLY numeric in volts
- current_source: { "dc_value": <number> }             — ONLY numeric in amps
- diode:          { "model": "<model_name>" }
- mosfet:         { "w": <number>, "l": <number>, "model": "<model_name>" }
- bjt:            { "model": "<model_name>" }
- opamp:          { "model": "<model_name>" }
    nodes format: ["output", "inverting_input", "non_inverting_input"]
    Example: U1 nodes ["Vout", "Vin-", "Vin+"]
STRICT PARAMETER RULES:
- The "parameters" object MUST contain ONLY the required key for that component type.
- NEVER put "description", "value", "note", "rating", "tolerance", or any free-text field inside "parameters".
- ALL parameter values MUST be numeric (int or float), NEVER strings.
- WRONG: { "resistance": "10k ohms" }  or  { "description": "5000 ohms" }
- RIGHT: { "resistance": 10000 }
###
ANALYSIS RULES:
EXPLICIT INTENT ALWAYS WINS. Map user keywords as follows:
- "transient" / "time domain" / "pulse" / "switching" → transient
- "AC" / "frequency response" / "Bode" / "filter"     → ac
- "DC operating point" / "bias point" / "quiescent"   → op
- "DC sweep"                                           → dc_sweep
If NO analysis is mentioned, infer EXACTLY ONE using this priority order:
  1. Reactive components present (capacitors or inductors) → ac
  2. Amplifier topology (BJT, MOSFET, op-amp)             → ac
  3. Time-domain keywords (pulse, clock, digital)          → transient
  4. Pure resistive / DC bias network                      → op
  5. Uncertain / fallback                                  → ac
NEVER leave "analyses" empty. NEVER output multiple analyses unless explicitly requested.
ANALYSIS SCHEMAS:
- AC:      { "type": "ac",        "parameters": { "start_freq": 1, "stop_freq": 100000, "num_points": 50 } }
- Transient: { "type": "transient", "parameters": { "tstart": 0, "tstop": 0.01, "tstep": 1e-5 } }
- DC Sweep:  { "type": "dc_sweep",  "parameters": { "source": "<V_name>", "start": 0, "stop": 5, "step": 0.1 } }
- DC:        { "type": "dc",        "parameters": { "source": "<V_name>", "start": 0, "stop": 5, "step": 0.1 } }
- Op Point:  { "type": "op" }
###
OUTPUT SCHEMA:
{
  "circuit_id": "<short_snake_case_id>",
  "title": "<3-8 word circuit name>",
  "description": "<user description verbatim>",
  "input_nodes": ["Vin"],
  "output_nodes": ["Vout"],
  "ground_node": "0",
  "components": [
    {
      "component_type": "resistor|capacitor|inductor|mosfet|bjt|opamp|voltage_source|current_source|diode",
      "name": "R1",
      "nodes": ["node_a", "node_b"],
      "parameters": { "resistance": 10000 },
      "model": null
    }
  ],
  "analyses": [
    { "type": "ac", "parameters": { "start_freq": 1, "stop_freq": 100000, "num_points": 50 } }
  ],
  "constraints": {},
  "topology_notes": "<brief explanation of topology choices>",
  "design_decisions": ["<decision 1>", "<decision 2>"],
  "summary": "<2-4 sentence plain English description>"
}
###
EXAMPLES:
--- EXAMPLE 1: Reactive circuit → AC analysis ---
Input: "RC low pass filter with 1k resistor and 1uF capacitor"
{
  "circuit_id": "rc_low_pass_filter",
  "title": "RC Low Pass Filter",
  "description": "RC low pass filter with 1k resistor and 1uF capacitor",
  "input_nodes": ["Vin"],
  "output_nodes": ["Vout"],
  "ground_node": "0",
  "components": [
    { "component_type": "voltage_source", "name": "V1", "nodes": ["Vin", "0"],    "parameters": { "dc_value": 1 },       "model": null },
    { "component_type": "resistor",       "name": "R1", "nodes": ["Vin", "Vout"], "parameters": { "resistance": 1000 },  "model": null },
    { "component_type": "capacitor",      "name": "C1", "nodes": ["Vout", "0"],   "parameters": { "capacitance": 1e-6 }, "model": null }
  ],
  "analyses": [
    { "type": "ac", "parameters": { "start_freq": 1, "stop_freq": 100000, "num_points": 50 } }
  ],
  "constraints": {},
  "topology_notes": "Series resistor and shunt capacitor form a first-order low-pass filter.",
  "design_decisions": ["Cutoff frequency ~159 Hz from R=1k, C=1uF", "AC analysis selected for frequency response"],
  "summary": "This is a first-order RC low-pass filter that passes low-frequency signals while attenuating higher frequencies. A resistor and capacitor form a frequency-dependent voltage divider. The cutoff frequency is approximately 159 Hz."
}
--- EXAMPLE 2: Pure resistive DC circuit → Operating Point ---
Input: "5V DC voltage divider with two equal resistors"
{
  "circuit_id": "dc_voltage_divider",
  "title": "DC Resistive Voltage Divider",
  "description": "5V DC voltage divider with two equal resistors",
  "input_nodes": ["Vin"],
  "output_nodes": ["Vmid"],
  "ground_node": "0",
  "components": [
    { "component_type": "voltage_source", "name": "V1", "nodes": ["Vin", "0"],    "parameters": { "dc_value": 5 },       "model": null },
    { "component_type": "resistor",       "name": "R1", "nodes": ["Vin", "Vmid"], "parameters": { "resistance": 10000 }, "model": null },
    { "component_type": "resistor",       "name": "R2", "nodes": ["Vmid", "0"],   "parameters": { "resistance": 10000 }, "model": null }
  ],
  "analyses": [
    { "type": "op" }
  ],
  "constraints": {},
  "topology_notes": "Two equal series resistors divide Vin evenly, producing Vmid = Vin/2.",
  "design_decisions": ["Equal resistors produce 2.5V at midpoint", "Operating point chosen for pure DC resistive circuit"],
  "summary": "This circuit is a resistive voltage divider powered by a 5V DC source. Two equal resistors in series split the supply voltage evenly, producing 2.5V at the midpoint. It contains no reactive components, making an operating point analysis appropriate."
}
###
PRE-OUTPUT CHECKLIST:
"title" present, non-empty, 3-8 words, reflects circuit type
"summary" present, 2-4 sentences, no SPICE syntax or node names
"analyses" has exactly one entry (unless user explicitly requested multiple)
Component names use sequential prefixed identifiers (R1, R2, C1, V1...)
Shared nodes use identical strings across all components referencing them
JSON is strictly valid — no trailing commas, no comments, all brackets closed
Ground node is "0" everywhere"""

    _REQUIRED_PARAMS_BY_TYPE = {
        "resistor": "resistance",
        "capacitor": "capacitance",
        "inductor": "inductance",
        "voltage_source": "dc_value",
        "current_source": "dc_value",
    }

    _DEFAULT_VALUES = {
        "resistor": 1000,
        "capacitor": 1e-6,
        "inductor": 1e-3,
        "voltage_source": 5,
        "current_source": 0.001,
    }

    @staticmethod
    def _extract_numeric(value) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            import re
            match = re.search(r"[\d.]+", value)
            if match:
                return float(match.group())
        return 0.0

    @classmethod
    def _fix_component_params(cls, comp: ComponentSpec) -> ComponentSpec:
        params = dict(comp.parameters)
        comp_type = comp.component_type.lower()
        required = cls._REQUIRED_PARAMS_BY_TYPE.get(comp_type)

        if required and required not in params:
            # Try to extract a numeric value from any wrong parameter
            for key, val in list(params.items()):
                if key in ("description", "value", "rating", "tolerance", "note"):
                    extracted = cls._extract_numeric(val)
                    if extracted > 0:
                        params[required] = extracted
                        del params[key]
                        break
            else:
                params[required] = cls._DEFAULT_VALUES.get(comp_type, 0)

        return ComponentSpec(
            component_type=comp.component_type,
            name=comp.name,
            nodes=list(comp.nodes),
            parameters=params,
            model=comp.model,
        )

    @classmethod
    def _apply_safety_fixes(cls, blueprint: CircuitBlueprint) -> CircuitBlueprint:
        fixed_components = [cls._fix_component_params(c) for c in blueprint.components]

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
            elif atype in ("dc", "dc_sweep"):
                params = analysis.setdefault("parameters", {})
                params.setdefault("source", "V1")
                params.setdefault("start", 0)
                params.setdefault("stop", 1)
                params.setdefault("step", 0.1)
            fixed_analyses.append(analysis)

        return CircuitBlueprint(
            circuit_id=blueprint.circuit_id,
            description=blueprint.description,
            title=blueprint.title,
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

    def create_plan(self, description: str, apply_safety_fixes: bool = True) -> CircuitBlueprint:
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

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\nRaw output:\n{raw[:500]}")
        blueprint = CircuitBlueprint(
            circuit_id=data.get("circuit_id", "unnamed"),
            description=data.get("description", ""),
            title=data.get("title", ""),
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
        if apply_safety_fixes:
            return self._apply_safety_fixes(blueprint)
        return blueprint

    def create_plan_strict(self, description: str) -> CircuitBlueprint:
        return self.create_plan(description, apply_safety_fixes=True)
