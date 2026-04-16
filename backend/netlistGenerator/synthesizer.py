from __future__ import annotations

import ast
import json
import textwrap
from dataclasses import dataclass, field
from typing import Any, Optional

from builder import CircuitBuilder
from planner import OpenCodeClient


_ALLOWED_BUILTINS: dict[str, Any] = {
    "print": print,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "None": None,
    "True": True,
    "False": False,
}

_FORBIDDEN_AST_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    ast.Nonlocal,
    ast.AsyncFunctionDef,
    ast.AsyncFor,
    ast.AsyncWith,
    ast.Await,
)

_FORBIDDEN_ATTRS = frozenset(
    {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__globals__",
        "__code__",
        "__closure__",
        "__builtins__",
        "system",
        "popen",
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "breakpoint",
    }
)


@dataclass
class ValidationError:
    kind: str
    message: str
    line: Optional[int] = None


@dataclass
class SynthesisResult:
    python_code: str
    netlist: Optional[str] = None
    synthesis_metadata: Optional[dict] = None
    validation_errors: list[ValidationError] = field(default_factory=list)
    repair_attempts: int = 0


class CodeValidator:
    _REQUIRED_CALLS = {"CircuitBuilder", "netlist"}

    def validate(self, code: str) -> list[ValidationError]:
        errors: list[ValidationError] = []
        tree = self._parse(code, errors)
        if tree is None:
            return errors

        self._check_forbidden_nodes(tree, errors)
        self._check_forbidden_attrs(tree, errors)
        self._check_required_calls(tree, errors)
        self._check_netlist_assignment(tree, errors)
        return errors

    @staticmethod
    def _parse(code: str, errors: list[ValidationError]) -> Optional[ast.Module]:
        try:
            return ast.parse(code)
        except SyntaxError as exc:
            errors.append(
                ValidationError(
                    kind="ast",
                    message=f"Syntax error: {exc.msg}",
                    line=exc.lineno,
                )
            )
            return None

    @staticmethod
    def _check_forbidden_nodes(tree: ast.Module, errors: list[ValidationError]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, _FORBIDDEN_AST_NODES):
                lineno = getattr(node, "lineno", None)
                errors.append(
                    ValidationError(
                        kind="ast",
                        message=f"Forbidden AST node '{type(node).__name__}'",
                        line=lineno,
                    )
                )

    @staticmethod
    def _check_forbidden_attrs(tree: ast.Module, errors: list[ValidationError]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in _FORBIDDEN_ATTRS:
                lineno = getattr(node, "lineno", None)
                errors.append(
                    ValidationError(
                        kind="ast",
                        message=f"Forbidden attribute access '.{node.attr}'",
                        line=lineno,
                    )
                )

    @staticmethod
    def _check_required_calls(tree: ast.Module, errors: list[ValidationError]) -> None:
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "CircuitBuilder":
                    found.add("CircuitBuilder")
                if isinstance(func, ast.Attribute) and func.attr == "netlist":
                    found.add("netlist")

        missing = CodeValidator._REQUIRED_CALLS - found
        for name in sorted(missing):
            errors.append(
                ValidationError(
                    kind="api",
                    message=f"Required call '{name}' not found",
                )
            )

    @staticmethod
    def _check_netlist_assignment(
        tree: ast.Module, errors: list[ValidationError]
    ) -> None:
        assigned_netlist = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "netlist":
                        assigned_netlist = True
                        break
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "netlist":
                    assigned_netlist = True

        if not assigned_netlist:
            errors.append(
                ValidationError(
                    kind="missing_netlist",
                    message="Generated code does not assign 'netlist' variable",
                )
            )


class RestrictedExecutor:
    def __init__(self, circuit_builder_class: type) -> None:
        self._CircuitBuilder = circuit_builder_class

    def execute(self, code: str) -> str:
        namespace: dict[str, Any] = {
            "__builtins__": _ALLOWED_BUILTINS,
            "CircuitBuilder": self._CircuitBuilder,
        }
        local_vars: dict[str, Any] = {}

        try:
            exec(compile(code, "<generated>", "exec"), namespace, local_vars)
        except Exception as exc:
            raise RuntimeError(f"Execution error: {exc}") from exc

        netlist = local_vars.get("netlist") or namespace.get("netlist")
        if netlist is None:
            raise RuntimeError(
                "Generated code executed but netlist variable is missing"
            )
        if not isinstance(netlist, str):
            raise RuntimeError(f"'netlist' must be str, got {type(netlist).__name__}")
        if not netlist.strip():
            raise RuntimeError("Generated netlist is empty")

        return netlist


_REPAIR_HINTS: dict[str, str] = {
    "missing_netlist": "Add `netlist = builder.netlist()` at the end of the script.",
    "api": "Instantiate CircuitBuilder() and call builder.netlist().",
    "ast": "Remove all import statements. CircuitBuilder is injected automatically.",
    "runtime": "Check method signatures and argument types.",
}


class RepairEngine:
    def __init__(self, llm_client: OpenCodeClient, system_prompt: str) -> None:
        self._llm = llm_client
        self._system_prompt = system_prompt

    def repair(
        self,
        code: str,
        errors: list[ValidationError],
        blueprint: dict,
    ) -> tuple[str, list[ValidationError]]:
        validator = CodeValidator()

        error_block = "\n".join(
            f"  [{e.kind}] line {e.line or '?'}: {e.message}" for e in errors
        )
        hints = set(e.kind for e in errors)
        hint_block = "\n".join(
            f"  • {_REPAIR_HINTS.get(k, '')}"
            for k in sorted(hints)
            if _REPAIR_HINTS.get(k)
        )

        repair_prompt = textwrap.dedent(f"""
            The following generated Python code has validation errors. Fix ONLY the errors.

            BLUEPRINT:
            {json.dumps(blueprint, indent=2)}

            CURRENT CODE:
            {code}

            VALIDATION ERRORS:
            {error_block}

            REPAIR HINTS:
            {hint_block}

            RULES:
            - Do NOT include any import statements (CircuitBuilder is injected automatically).
            - The script MUST end with: netlist = builder.netlist()
            - Return ONLY the corrected Python code, no markdown.
        """).strip()

        try:
            raw = self._llm.generate(
                system_prompt=self._system_prompt,
                user_prompt=repair_prompt,
                response_format="text",
            )
            patched = self._strip_code_fences(raw)
        except Exception as exc:
            return code, errors

        new_errors = validator.validate(patched)
        if len(new_errors) < len(errors):
            return patched, new_errors

        return code, errors

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text


class SpecialistSynthesizer:
    SYSTEM_PROMPT = """You are the Specialist Synthesizer in SPACY. Your role is to transform a validated circuit blueprint into clean, executable Python code that builds an LTspice-compatible SPICE netlist.

OUTPUT REQUIREMENTS:
- Return ONLY valid Python code — no markdown, no explanation, no preamble.
- Do NOT include any import statements. CircuitBuilder is injected into your scope automatically.
- The code must instantiate CircuitBuilder and produce a `netlist` string as the final variable.
- Follow SPICE/LTspice conventions: proper node names, device prefixes, SPICE syntax.
- Include all components with correct parameters and node connections.
- Add ONLY the analysis requested in the blueprint (one of .AC, .DC, .TRAN, .OP, or .DC_SWEEP).

NAMING RULE (CRITICAL):
- Component names MUST include explicit prefixes: V1, R1, C1, L1, I1, D1, M1, Q1, U1, etc.
- Do NOT use bare numbers like "1" — always use "V1", "R1", "C1", etc.
- Example: builder.resistor("R1", "n1", "n2", "1k") → produces "R1 n1 n2 1k"
- Example: builder.voltage_source("V1", "in", "0", dc=5) → produces "V1 in 0 DC 5"

TITLE RULE:
- Use builder.title() with clean, trimmed text (no extra whitespace)
- Example: builder.title("RC low pass filter") — NOT "  RC low pass filter  "

ANALYSIS RULE:
- Include ONLY the analysis type specified in the blueprint
- For AC analysis: builder.ac_analysis(1, 1000000, 100)
- Do NOT add extra analyses unless explicitly requested

PYTHON CIRCUIT BUILDER API:
- builder = CircuitBuilder()
- builder.title("title")
- builder.comment("comment")
- builder.resistor(name, n1, n2, value)
- builder.capacitor(name, n1, n2, value)
- builder.inductor(name, n1, n2, value)
- builder.voltage_source(name, n1, n2, dc=val, ac=val, pulse=..., sine=...)
- builder.current_source(name, n1, n2, dc=val)
- builder.diode(name, n1, n2, model)
- builder.mosfet(name, nd, ng, ns, nb, model, w=val, l=val)
- builder.bjt(name, nc, nb, ne, model)
- builder.opamp(name, nout, ninv, nnoninv)
- builder.subcircuit(name, nodes, subckt_name)
- builder.model(name, model_type, **params)
- builder.global_node(node)
- builder.ac_analysis(start_freq, stop_freq, num_points, sweep_type)
- builder.dc_sweep(source, start, stop, increment)
- builder.transient(tstart, tstop, tstep)
- builder.operating_point()
- netlist = builder.netlist()   ← REQUIRED final line

Return only the Python code. No markdown fences, no explanation."""

    _COMPONENT_PREFIXES = ("R", "C", "L", "V", "I", "D", "M", "Q", "U")

    @staticmethod
    def _normalize_component_name(name: str) -> str:
        name = name.lstrip("RCLVIDMQ")
        if not name:
            name = "1"
        return name

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2500,
    ):
        self._llm_client = OpenCodeClient(
            api_key=api_key,
            api_base=api_base,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._validator = CodeValidator()
        self._executor = RestrictedExecutor(circuit_builder_class=CircuitBuilder)
        self._repair_engine = RepairEngine(
            llm_client=self._llm_client,
            system_prompt=self.SYSTEM_PROMPT,
        )

    def _normalize_code(self, code: str) -> str:
        return code

    def generate_python_code(self, blueprint: dict) -> str:
        prompt = self._build_generation_prompt(blueprint)
        raw = self._llm_client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            response_format="text",
        )
        code = self._strip_code_fences(raw)
        return self._normalize_code(code)

    def synthesize(self, blueprint: dict) -> SynthesisResult:
        python_code = self.generate_python_code(blueprint)

        errors = self._validator.validate(python_code)
        repair_rounds = 0

        if errors and repair_rounds < 1:
            python_code, errors = self._repair_engine.repair(
                code=python_code,
                errors=errors,
                blueprint=blueprint,
            )
            repair_rounds += 1

        if errors:
            error_summary = "; ".join(f"[{e.kind}] {e.message}" for e in errors)
            raise RuntimeError(f"Code validation failed: {error_summary}")

        try:
            netlist = self._executor.execute(python_code)
        except RuntimeError as exc:
            if repair_rounds < 1:
                python_code, remaining = self._repair_engine.repair(
                    code=python_code,
                    errors=[ValidationError(kind="runtime", message=str(exc))],
                    blueprint=blueprint,
                )
                repair_rounds += 1
                if not remaining:
                    netlist = self._executor.execute(python_code)
                else:
                    raise RuntimeError(f"Runtime error persisted: {exc}") from exc
            else:
                raise RuntimeError(
                    f"Runtime error persisted after repair: {exc}"
                ) from exc

        return SynthesisResult(
            python_code=python_code,
            netlist=netlist,
            synthesis_metadata={
                "blueprint_id": blueprint.get("circuit_id", "unknown"),
                "code_length": len(python_code),
                "netlist_length": len(netlist),
                "repair_rounds": repair_rounds,
            },
            repair_attempts=repair_rounds,
        )

    @staticmethod
    def _build_generation_prompt(blueprint: dict) -> str:
        analyses = blueprint.get("analyses", [])
        analysis_info = ""
        if analyses:
            a = analyses[0]
            atype = a.get("type", "").lower()
            params = a.get("parameters", {})
            if atype == "ac":
                analysis_info = f"Use: builder.ac_analysis({params.get('start_freq', 1)}, {params.get('stop_freq', 1000000)}, {params.get('num_points', 100)})"
            elif atype == "transient":
                analysis_info = f"Use: builder.transient({params.get('tstart', 0)}, {params.get('tstop', 0.001)}, {params.get('tstep', 0.000001)})"
            elif atype == "dc":
                analysis_info = f"Use: builder.dc_sweep('{params.get('source', 'V1')}', {params.get('start', 0)}, {params.get('stop', 1)}, {params.get('step', 0.1)})"
            elif atype == "op":
                analysis_info = "Use: builder.operating_point()"
            elif atype == "dc_sweep":
                analysis_info = f"Use: builder.dc_sweep('{params.get('source', 'V1')}', {params.get('start', 0)}, {params.get('stop', 1)}, {params.get('step', 0.1)})"

        return textwrap.dedent(f"""
            Transform this validated circuit blueprint into Python code using the CircuitBuilder API.

            BLUEPRINT:
            {json.dumps(blueprint, indent=2)}

            Generate clean, executable Python code that:
            1. Creates a CircuitBuilder instance: builder = CircuitBuilder()
            2. Sets title with builder.title("description") — trim whitespace
            3. Defines any required .MODEL statements for active devices
            4. Adds all components with proper node connections
            5. Adds ONE analysis only: {analysis_info}
            6. Ends with: netlist = builder.netlist()

            CRITICAL RULES:
            - Do NOT add any import statements.
            - Use explicit component names with prefixes: V1, R1, C1, L1, etc. (NOT "1", "2", etc.)
            - Node names must match the blueprint exactly.
            - Use proper SPICE value strings (e.g. "1k", "1u", "100n").
            - Do NOT add extra analyses.
        """).strip()

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text


def synthesize_circuit(blueprint: dict) -> SynthesisResult:
    synthesizer = SpecialistSynthesizer()
    return synthesizer.synthesize(blueprint)
