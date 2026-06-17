from __future__ import annotations

import json
import re
from typing import Optional

from app.models.pipeline_models import ClarificationResult
from app.services.circuit_planner import OpenCodeClient


_MISSING_SOURCE = re.compile(
    r"(?!(?:.*\b(?:voltage|current)\s*source|V\d+|I\d+))",
    re.IGNORECASE,
)

_MISSING_GROUND_WORDS = {"ground", "gnd", "0", "reference"}


class ClarificationEngine:
    def __init__(self, llm_client: Optional[OpenCodeClient] = None):
        self._llm = llm_client

    def analyze(self, prompt: str) -> ClarificationResult:
        questions: list[str] = []
        stripped = prompt.strip().lower()

        if not self._has_source(stripped):
            questions.append(
                "What type of source should power the circuit (voltage/current) and what value?"
            )

        if not self._has_ground_reference(stripped):
            questions.append("Where should the ground reference be connected?")

        if not self._has_component_values(stripped):
            questions.append(
                "Please specify component values (e.g., resistor in ohms, capacitor in farads)."
            )

        if not self._has_analysis_type(stripped):
            questions.append(
                "What type of analysis would you like? (AC frequency response, transient time-domain, or DC operating point)"
            )

        return ClarificationResult(
            needs_clarification=len(questions) > 0,
            questions=questions,
        )

    def _has_source(self, text: str) -> bool:
        return bool(re.search(r"\b(v\d+|i\d+|voltage|current|source|supply|vcc|vdd|vee|vss)\b", text, re.IGNORECASE))

    def _has_ground_reference(self, text: str) -> bool:
        return any(w in text for w in _MISSING_GROUND_WORDS)

    def _has_component_values(self, text: str) -> bool:
        return bool(re.search(
            r"\b(\d+\.?\d*\s*(?:k|meg|m|u|n|p|ohm|f|h|w)?)\b",
            text,
            re.IGNORECASE,
        ))

    def _has_analysis_type(self, text: str) -> bool:
        return bool(re.search(
            r"\b(ac|transient|dc|op|frequency|bode|time.domain|sweep)\b",
            text,
            re.IGNORECASE,
        ))

    def llm_clarify(self, prompt: str, blueprint: dict) -> ClarificationResult:
        if self._llm is None:
            return ClarificationResult(needs_clarification=False)

        system = (
            "You are a clarification engine for circuit design. "
            "Given a user prompt and a partial blueprint, determine if more information is needed.\n"
            "Return ONLY JSON: {\"needs_clarification\": bool, \"questions\": [\"...\"]}"
        )
        try:
            raw = self._llm.generate(
                system_prompt=system,
                user_prompt=json.dumps({"prompt": prompt, "partial_blueprint": blueprint}),
                response_format="json",
                temperature=0.1,
                max_tokens=200,
            )
            data = json.loads(raw)
            return ClarificationResult(
                needs_clarification=data.get("needs_clarification", False),
                questions=data.get("questions", []),
            )
        except Exception:
            return ClarificationResult(needs_clarification=False)
