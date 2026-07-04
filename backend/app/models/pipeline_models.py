from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class IntentType(str, Enum):
    CREATE_CIRCUIT = "CREATE_CIRCUIT"
    MODIFY_CIRCUIT = "MODIFY_CIRCUIT"
    EXPLAIN_CIRCUIT = "EXPLAIN_CIRCUIT"


@dataclass
class IntentResult:
    intent: IntentType
    is_question: bool = False
    validation_questions: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class SynthesisResult:
    netlist: str
    synthesis_time_ms: float = 0.0
    component_count: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class SimulationDiagnostic:
    category: str
    message: str
    severity: str = "warning"


@dataclass
class SimulationResult:
    success: bool
    analyses: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    returncode: Optional[int] = None
    diagnostics: list[SimulationDiagnostic] = field(default_factory=list)
    convergence_failures: list[str] = field(default_factory=list)


@dataclass
class ResolverResult:
    resolved: bool
    patch_description: str = ""
    retry_count: int = 0
    patched_blueprint: Optional[dict] = None
    patched_netlist: Optional[str] = None
    errors_remaining: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    success: bool
    intent: Optional[IntentResult] = None
    blueprint: Optional[dict] = None
    validation: Optional[Any] = None
    synthesis: Optional[SynthesisResult] = None
    simulation: Optional[SimulationResult] = None
    resolution: Optional[ResolverResult] = None
    title: str = ""
    summary: str = ""
    error: Optional[str] = None
    clarifications: list[str] = field(default_factory=list)
    changes_summary: Optional[str] = None


@dataclass
class ClarificationResult:
    needs_clarification: bool
    questions: list[str] = field(default_factory=list)
    partial_blueprint: Optional[dict] = None


def format_spice_value(value: float) -> str:
    if value == 0.0:
        return "0"
    abs_val = abs(value)
    if abs_val >= 1_000_000:
        return f"{value / 1_000_000:g}meg"
    if abs_val >= 1_000:
        return f"{value / 1_000:g}k"
    if abs_val >= 0.1:
        return f"{value:g}"
    if abs_val >= 1e-3:
        return f"{value * 1_000:g}m"
    if abs_val >= 1e-6:
        return f"{value * 1_000_000:g}u"
    if abs_val >= 1e-9:
        return f"{value * 1_000_000_000:g}n"
    return f"{value * 1_000_000_000_000:g}p"


def parse_spice_value_to_float(text: str) -> float:
    suffixes = {
        "t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3,
        "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15,
    }
    token = text.strip().lower()
    for suffix, multiplier in sorted(suffixes.items(), key=lambda item: -len(item[0])):
        if token.endswith(suffix):
            return float(token[: -len(suffix)]) * multiplier
    return float(token)
