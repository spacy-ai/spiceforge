# Planner - Core Reasoning Agent for SPACY.

from __future__ import annotations
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

import requests

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    AC = "ac"
    DC = "dc"
    TRANSIENT = "transient"
    OPERATING_POINT = "op"
    DC_SWEEP = "dc_sweep"


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


@dataclass
class PlannerState:
    current_plan: Optional[CircuitBlueprint] = None
    previous_plans: list[CircuitBlueprint] = field(default_factory=list)
    previous_netlists: list[str] = field(default_factory=list)
    repair_attempts: list[dict] = field(default_factory=list)
    synthesis_history: list[dict] = field(default_factory=list)


# OpenCode LLM Client

class OpenCodeClient:

    #SET IN ENV:  OPENCODE_API_KEY, OPENCODE_API_BASE, OPENCODE_MODEL

    DEFAULT_BASE = "https://opencode.ai/zen/v1"
    DEFAULT_MODEL = "minimax-m2.5-free"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenCode API key is required. Set OPENCODE_API_KEY env var."
            )

        self.api_base = (api_base or os.environ.get("OPENCODE_API_BASE", self.DEFAULT_BASE)).rstrip("/")
        self.model = model or os.environ.get("OPENCODE_MODEL", self.DEFAULT_MODEL)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

   

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
                {"role": "user",   "content": user_prompt},
            ],
            "max_tokens":  max_tokens  or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "OpenCode request (attempt %d/%d) model=%s",
                    attempt, self.max_retries, self.model,
                )
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

                logger.debug("OpenCode response received (%d chars)", len(content))
                return content

            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "?"
                logger.warning("HTTP %s on attempt %d: %s", status, attempt, exc)
                last_error = exc
                # Don't retry on client errors.
                if exc.response is not None and exc.response.status_code not in (429, 500, 502, 503, 504):
                    raise

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                logger.warning("Network error on attempt %d: %s", attempt, exc)
                last_error = exc

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)  # exponential-ish back-off

        raise RuntimeError(
            f"OpenCode API failed after {self.max_retries} attempts: {last_error}"
        )

    # Helpers
    
    @staticmethod
    def _strip_json_fences(text: str) -> str:
        # Remove ```json ... ``` or ``` ... ``` fences if present
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # drop opening fence
            lines = lines[1:] if lines[0].startswith("```") else lines
            # drop closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text


# Planner

class Planner:
    # Core reasoning agent for SPACY.
    # Converts natural lang circuit descriptions into structured CircuitBlueprint objects by reasoning through the OpenCode LLM API.

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        self.state = PlannerState()
        self._system_prompt = self._build_system_prompt()

        self.llm_client = OpenCodeClient(
            api_key=api_key,
            api_base=api_base,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # System prompt
    @staticmethod
    def _build_system_prompt() -> str:
        return """You are the Planner in the SPACY multi-agent circuit design system. Your role is to analyze natural language circuit descriptions and create detailed circuit blueprints that specify components, topology, and analysis requirements.
STRICT OUTPUT RULES:
- Return ONLY a valid JSON object — no markdown, no explanation, no preamble.
- All node names must be consistent strings that comply with SPICE/LTspice conventions.
- Ground must always be node "0".
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
  "design_decisions": ["<decision 1>", "<decision 2>"]
}"""

    # Public API

    def _llm_reasoning(self, prompt: str) -> CircuitBlueprint:
        #Send prompt to OpenCode and parse the JSON response into a CircuitBlueprint.
        logger.info("Calling OpenCode LLM (model=%s)", self.llm_client.model)

        try:
            raw = self.llm_client.generate(
                system_prompt=self._system_prompt,
                user_prompt=prompt,
                response_format="json",
            )
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            raise RuntimeError(f"Failed to get blueprint from LLM: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("JSON decode failed. Raw response:\n%s", raw)
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        try:
            return CircuitBlueprint(
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
            )
        except (TypeError, KeyError) as exc:
            logger.error("Blueprint construction failed: %s\nData: %s", exc, data)
            raise ValueError(f"Malformed blueprint data from LLM: {exc}") from exc


    def create_plan(self, description: str) -> CircuitBlueprint:
        #Create a CircuitBlueprint from a natural-language description
        prompt = (
            f"Analyze the following circuit description and return a complete JSON blueprint.\n\n"
            f"DESCRIPTION:\n{description}\n\n"
            f"Include every component with correct node connections, all required analyses, "
            f"design constraints, and brief reasoning for your topology choices."
        )
        blueprint = self._llm_reasoning(prompt)
        self.state.current_plan = blueprint
        self.state.previous_plans.append(blueprint)
        logger.info("Plan created: %s (%d components)", blueprint.circuit_id, len(blueprint.components))
        return blueprint
    
    def _incorporate_feedback(
        self, blueprint: CircuitBlueprint, feedback: dict
    ) -> CircuitBlueprint:
        # Append a structured repair note to topology notes
        error_type = feedback.get("error_type", "unknown")
        message = feedback.get("message", "")
        tag_map = {
            "convergence": "[REPAIR:CONVERGENCE]",
            "floating":    "[REPAIR:FLOATING_NODE]",
            "syntax":      "[REPAIR:SYNTAX]",
            "model":       "[REPAIR:MODEL]",
        }
        tag = next((v for k, v in tag_map.items() if k in error_type.lower()), "[REPAIR]")
        blueprint.topology_notes += f"\n{tag} {message}"
        return blueprint
    
    def update_plan(
        self,
        blueprint: CircuitBlueprint,
        repair_feedback: Optional[dict] = None,
    ) -> CircuitBlueprint:
        # Update the current plan
        if repair_feedback:
            self.state.repair_attempts.append(repair_feedback)
            blueprint = self._incorporate_feedback(blueprint, repair_feedback)

        self.state.current_plan = blueprint
        return blueprint

    def repair_plan(self, blueprint: CircuitBlueprint, feedback: dict) -> CircuitBlueprint:
        # Ask the LLM to produce a repaired blueprint given structured feedback. Returns new CircuitBlueprint not patch notes.

        self.state.repair_attempts.append(feedback)
        prompt = (
            f"The following circuit blueprint produced a simulation error.\n\n"
            f"BLUEPRINT:\n{json.dumps(asdict(blueprint), indent=2)}\n\n"
            f"ERROR FEEDBACK:\n{json.dumps(feedback, indent=2)}\n\n"
            f"Return a corrected JSON blueprint that resolves the error. "
            f"Do not repeat the same mistake."
        )
        repaired = self._llm_reasoning(prompt)
        self.state.current_plan = repaired
        self.state.previous_plans.append(repaired)
        logger.info("Repaired plan created: %s", repaired.circuit_id)
        return repaired

    # State helpers

    def get_previous_plan(self, index: int = -1) -> Optional[CircuitBlueprint]:
        if -len(self.state.previous_plans) <= index < len(self.state.previous_plans):
            return self.state.previous_plans[index]
        return None

    def store_netlist(self, netlist: str) -> None:
        self.state.previous_netlists.append(netlist)

    def get_last_netlist(self) -> Optional[str]:
        return self.state.previous_netlists[-1] if self.state.previous_netlists else None

    def reset_state(self) -> None:
        self.state = PlannerState()
        logger.info("Planner state reset.")

    def to_dict(self) -> dict:
        return {
            "current_plan": asdict(self.state.current_plan) if self.state.current_plan else None,
            "plan_count": len(self.state.previous_plans),
            "netlist_count": len(self.state.previous_netlists),
            "repair_attempts": len(self.state.repair_attempts),
        }
    
