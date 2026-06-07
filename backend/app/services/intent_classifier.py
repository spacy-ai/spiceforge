from __future__ import annotations

import json
import re
from typing import Optional

from app.models.pipeline_models import IntentResult, IntentType
from app.services.circuit_planner import OpenCodeClient


_QUESTION_PATTERNS = re.compile(
    r"^(what|how|why|when|where|who|can you|tell me|explain|describe|define|is it)",
    re.IGNORECASE,
)

_CREATE_PATTERNS = re.compile(
    r"(create|design|make|build|generate|implement|construct|synthesize|produce|layout)",
    re.IGNORECASE,
)

_MODIFY_PATTERNS = re.compile(
    r"(modify|change|update|edit|add|remove|replace|adjust|tune|alter|swap|insert|delete|reconfigur)",
    re.IGNORECASE,
)

_EXPLAIN_PATTERNS = re.compile(
    r"(explain|describe|analyze|what does|how does|tell me about|interpret)",
    re.IGNORECASE,
)


class IntentClassifier:
    def __init__(self, llm_client: Optional[OpenCodeClient] = None):
        self._llm = llm_client

    def classify(self, prompt: str) -> IntentResult:
        result = self._rule_based(prompt)
        if result.intent != IntentType.CREATE_CIRCUIT or result.confidence >= 0.8:
            return result
        if self._llm is not None:
            return self._llm_fallback(prompt)
        return result

    def _rule_based(self, prompt: str) -> IntentResult:
        stripped = prompt.strip()
        is_question = bool(_QUESTION_PATTERNS.match(stripped))

        has_create = bool(_CREATE_PATTERNS.search(stripped))
        has_modify = bool(_MODIFY_PATTERNS.search(stripped))
        has_explain = bool(_EXPLAIN_PATTERNS.search(stripped))

        if has_create and not has_modify and not has_explain:
            return IntentResult(
                intent=IntentType.CREATE_CIRCUIT,
                is_question=is_question,
                confidence=0.9,
            )

        if has_modify and not has_create:
            return IntentResult(
                intent=IntentType.MODIFY_CIRCUIT,
                is_question=is_question,
                confidence=0.85,
            )

        if has_explain or is_question:
            return IntentResult(
                intent=IntentType.EXPLAIN_CIRCUIT,
                is_question=is_question,
                confidence=0.8,
            )

        if has_create and has_modify:
            mod_pos = stripped.lower().find(
                [m for m in ["modify", "change", "update", "edit"] if m in stripped.lower()][0]
            ) if any(m in stripped.lower() for m in ["modify", "change", "update", "edit"]) else -1
            create_pos = stripped.lower().find(
                [c for c in ["create", "design", "make", "build"] if c in stripped.lower()][0]
            ) if any(c in stripped.lower() for c in ["create", "design", "make", "build"]) else -1

            if mod_pos >= 0 and (create_pos < 0 or mod_pos < create_pos):
                return IntentResult(
                    intent=IntentType.MODIFY_CIRCUIT,
                    is_question=is_question,
                    confidence=0.75,
                )

        return IntentResult(
            intent=IntentType.CREATE_CIRCUIT,
            is_question=is_question,
            confidence=0.6,
        )

    def _llm_fallback(self, prompt: str) -> IntentResult:
        if self._llm is None:
            return IntentResult(
                intent=IntentType.CREATE_CIRCUIT,
                is_question=False,
                confidence=0.5,
            )

        system = (
            "You are an intent classifier for a circuit design system. "
            "Classify the user's intent as exactly one of: "
            "CREATE_CIRCUIT, MODIFY_CIRCUIT, EXPLAIN_CIRCUIT.\n\n"
            "Rules:\n"
            "- CREATE_CIRCUIT: user wants to design/build/generate a new circuit\n"
            "- MODIFY_CIRCUIT: user wants to change an existing circuit parameter/value/component\n"
            "- EXPLAIN_CIRCUIT: user asks a question about circuits or how something works\n\n"
            "Return ONLY valid JSON: {\"intent\": \"CREATE_CIRCUIT\", \"is_question\": false}"
        )

        try:
            raw = self._llm.generate(
                system_prompt=system,
                user_prompt=f"Classify this prompt: {prompt}",
                response_format="json",
                temperature=0.1,
                max_tokens=100,
            )
            data = json.loads(raw)
            return IntentResult(
                intent=IntentType(data.get("intent", "CREATE_CIRCUIT")),
                is_question=data.get("is_question", False),
                confidence=0.95,
            )
        except Exception:
            return IntentResult(
                intent=IntentType.CREATE_CIRCUIT,
                is_question=False,
                confidence=0.5,
            )


def classify_intent(prompt: str, llm_client: Optional[OpenCodeClient] = None) -> IntentResult:
    return IntentClassifier(llm_client=llm_client).classify(prompt)
