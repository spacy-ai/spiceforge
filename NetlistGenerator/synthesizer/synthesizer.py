from __future__ import annotations

import ast
import json
import logging
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)
# restrictions
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
        "__class__", "__bases__", "__subclasses__", "__mro__",
        "__globals__", "__code__", "__closure__", "__builtins__",
        "system", "popen", "eval", "exec", "compile",
        "open", "input", "breakpoint",
    }
)


# Data classes

@dataclass
class ValidationError:
    kind: str          # ast,api,missing netlist, runtime
    message: str
    line: Optional[int] = None


@dataclass
class SynthesisResult:
    python_code: str
    netlist: Optional[str] = None
    synthesis_metadata: Optional[dict] = None
    validation_errors: list[ValidationError] = field(default_factory=list)
    repair_attempts: int = 0


# ast code validator
class CodeValidator:
    """
    Validates LLM-generated code before execution - Parses the source into an AST, Walks the AST to block dangerous constructs, Checks that required CircuitBuilder API calls are present, Ensures the last assignment is `netlist = builder.netlist()`.
    """

    _REQUIRED_CALLS = {"CircuitBuilder", "netlist"}

    def validate(self, code: str) -> list[ValidationError]:
        errors: list[ValidationError] = []
        tree = self._parse(code, errors)
        if tree is None:
            return errors  # if syntax error, no point in continuing

        self._check_forbidden_nodes(tree, errors)
        self._check_forbidden_attrs(tree, errors)
        self._check_required_calls(tree, errors)
        self._check_netlist_assignment(tree, errors)
        return errors

    # Internal helpers

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
                        message=f"Forbidden AST node '{type(node).__name__}' is not allowed in generated code.",
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
                        message=f"Forbidden attribute access '.{node.attr}' detected.",
                        line=lineno,
                    )
                )

    @staticmethod
    def _check_required_calls(tree: ast.Module, errors: list[ValidationError]) -> None:
        """Ensure that CircuitBuilder is instantiated and .netlist() is called."""
        found: set[str] = set()
        for node in ast.walk(tree):
            # CircuitBuilder() call
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "CircuitBuilder":
                    found.add("CircuitBuilder")
                # builder.netlist() call
                if isinstance(func, ast.Attribute) and func.attr == "netlist":
                    found.add("netlist")

        missing = CodeValidator._REQUIRED_CALLS - found
        for name in sorted(missing):
            errors.append(
                ValidationError(
                    kind="api",
                    message=f"Required call '{name}' not found in generated code.",
                )
            )

    @staticmethod
    def _check_netlist_assignment(tree: ast.Module, errors: list[ValidationError]) -> None:
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
                    message="Generated code does not assign the variable 'netlist'.",
                )
            )


# Restricted executor

class RestrictedExecutor:

    def __init__(self, circuit_builder_class: type) -> None:
        self._CircuitBuilder = circuit_builder_class

    def execute(self, code: str) -> str:
        """
        run code and return the value of netlist variable
        """
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
                "Generated code executed successfully but netlist variable is missing."
            )
        if not isinstance(netlist, str):
            raise RuntimeError(
                f"'netlist' must be a str, got {type(netlist).__name__}."
            )
        if not netlist.strip():
            raise RuntimeError("'netlist' is an empty string — netlist generation failed.")

        return netlist


# Partial repair engine

_REPAIR_HINTS: dict[str, str] = {
    "missing_netlist": (
        "The code is missing a `netlist = builder.netlist()` assignment. "
        "Add it at the end of the script."
    ),
    "api": (
        "One or more required CircuitBuilder API calls are absent. "
        "Make sure to instantiate CircuitBuilder() and call builder.netlist()."
    ),
    "ast": (
        "The code contains forbidden constructs (import statements, dangerous attributes). "
        "Remove all `import` / `from ... import` lines — CircuitBuilder is provided automatically. "
        "Do not use __builtins__, open(), exec(), eval(), or os/sys modules."
    ),
    "runtime": (
        "The code raises a runtime exception when executed. "
        "Check method signatures and argument types against the CircuitBuilder API."
    ),
}


class RepairEngine:
    """
    Attempts incremental correction of generated code.
    """

    def __init__(self, llm_client: Any, system_prompt: str, max_repair_attempts: int = 2) -> None:
        self._llm = llm_client
        self._system_prompt = system_prompt
        self._max_attempts = max_repair_attempts

    def repair(
        self,
        code: str,
        errors: list[ValidationError],
        blueprint: dict,
    ) -> tuple[str, list[ValidationError], int]:
        """
        return repaired code, error, total repair round
        """
        validator = CodeValidator()
        current_code = code
        current_errors = errors
        rounds = 0

        while current_errors and rounds < self._max_attempts:
            rounds += 1
            repair_prompt = self._build_repair_prompt(current_code, current_errors, blueprint)
            try:
                raw = self._llm.generate(
                    system_prompt=self._system_prompt,
                    user_prompt=repair_prompt,
                    response_format="text",
                )
                patched = _strip_code_fences(raw)
            except Exception as exc:
                logger.warning("Repair LLM call failed (round %d): %s", rounds, exc)
                break

            new_errors = validator.validate(patched)
            if len(new_errors) < len(current_errors):
                # keep patched version even if not perfect
                current_code = patched
                current_errors = new_errors
                logger.info(
                    "Repair round %d: errors reduced %d → %d",
                    rounds, len(errors), len(new_errors),
                )
            else:
                logger.warning(
                    "Repair round %d produced no improvement; stopping.", rounds
                )
                break

        return current_code, current_errors, rounds

    @staticmethod
    def _build_repair_prompt(
        code: str, errors: list[ValidationError], blueprint: dict
    ) -> str:
        error_block = "\n".join(
            f"  [{e.kind}] line {e.line or '?'}: {e.message}" for e in errors
        )
        hints = set(e.kind for e in errors)
        hint_block = "\n".join(
            f"  • {_REPAIR_HINTS.get(k, '')}" for k in sorted(hints) if _REPAIR_HINTS.get(k)
        )

        return textwrap.dedent(f"""
            The following generated Python code has validation errors. Fix ONLY the errors listed.
            Do NOT regenerate the whole circuit from scratch — preserve working parts.

            BLUEPRINT (for reference):
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
            - Return ONLY the corrected Python code, no markdown, no explanation.
        """).strip()


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


# Main synthesizer

class SpecialistSynthesizer:

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2500,
        max_repair_attempts: int = 2,
    ):
        from planner.planner import OpenCodeClient
        from NetlistGenerator.synthesizer.builder import CircuitBuilder

        self._llm_client = OpenCodeClient(
            api_key=api_key,
            api_base=api_base,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._system_prompt = self._build_system_prompt()
        self._validator = CodeValidator()
        self._executor = RestrictedExecutor(circuit_builder_class=CircuitBuilder)
        self._repair_engine = RepairEngine(
            llm_client=self._llm_client,
            system_prompt=self._system_prompt,
            max_repair_attempts=max_repair_attempts,
        )

    # System prompt

    @staticmethod
    def _build_system_prompt() -> str:
        return """You are the Specialist Synthesizer in SPACY. Your role is to transform a validated circuit blueprint into clean, executable Python code that builds an LTspice-compatible SPICE netlist.

OUTPUT REQUIREMENTS:
- Return ONLY valid Python code — no markdown, no explanation, no preamble.
- Do NOT include any import statements. CircuitBuilder is injected into your scope automatically.
- The code must instantiate CircuitBuilder and produce a `netlist` string as the final variable.
- Follow AnalogCoder conventions: proper node names, device prefixes, SPICE syntax.
- Include all components with correct parameters and node connections.
- Add required .AC, .DC, .TRAN, .OP, or .DC_SWEEP analysis directives.

PYTHON CIRCUIT BUILDER API (use these functions exactly):
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

EXAMPLE OUTPUT:
builder = CircuitBuilder()
builder.title("RC Low-Pass Filter")
builder.global_node("0")
builder.resistor("R1", "in", "out", "10k")
builder.capacitor("C1", "out", "0", "1u")
builder.voltage_source("V1", "in", "0", dc=5.0)
builder.transient(tstart=0, tstop=1e-3, tstep=1e-6)
netlist = builder.netlist()

Return only the Python code. No markdown fences, no explanation."""

    # Public API

    def generate_python_code(self, blueprint: dict) -> str:
        logger.info(
            "Generating Python code from blueprint: %s",
            blueprint.get("circuit_id", "unknown"),
        )
        prompt = self._build_generation_prompt(blueprint)
        try:
            raw = self._llm_client.generate(
                system_prompt=self._system_prompt,
                user_prompt=prompt,
                response_format="text",
            )
            code = _strip_code_fences(raw)
            logger.debug("Generated Python code (%d chars)", len(code))
            return code
        except Exception as exc:
            logger.error("Python code generation failed: %s", exc)
            raise RuntimeError(f"Failed to generate Python code: {exc}") from exc

    def synthesize(self, blueprint: dict) -> SynthesisResult:
        """
        Complete Pipeline
        1. Generate Python code from blueprint.
        2. Validate with AST checker.
        3. If validation errors exist, attempt incremental repair (up to max_repair_attempts).
        4. Execute in restricted sandbox.
        5. Return SynthesisResult.
        """
        # generate
        python_code = self.generate_python_code(blueprint)

        # validate
        errors = self._validator.validate(python_code)
        repair_rounds = 0

        # repair if needed
        if errors:
            logger.warning(
                "%d validation error(s) after generation — attempting repair.", len(errors)
            )
            python_code, errors, repair_rounds = self._repair_engine.repair(
                code=python_code,
                errors=errors,
                blueprint=blueprint,
            )

        if errors:
            error_summary = "; ".join(f"[{e.kind}] {e.message}" for e in errors)
            raise RuntimeError(
                f"Code validation failed after {repair_rounds} repair attempt(s): {error_summary}"
            )

        # execute in sandbox
        try:
            netlist = self._executor.execute(python_code)
        except RuntimeError as exc:
            # runtime error is treated as repairable and attempted one repair pass
            runtime_error = [ValidationError(kind="runtime", message=str(exc))]
            logger.warning("Runtime error — attempting one repair pass: %s", exc)
            repaired_code, remaining, extra_rounds = self._repair_engine.repair(
                code=python_code,
                errors=runtime_error,
                blueprint=blueprint,
            )
            repair_rounds += extra_rounds

            if remaining:
                raise RuntimeError(
                    f"Runtime error persisted after repair: {exc}"
                ) from exc

            netlist = self._executor.execute(repaired_code)
            python_code = repaired_code

        logger.info("Synthesis complete: netlist (%d chars)", len(netlist))
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
        return textwrap.dedent(f"""
            Transform this validated circuit blueprint into Python code using the CircuitBuilder API.

            BLUEPRINT:
            {json.dumps(blueprint, indent=2)}

            Generate clean, executable Python code that:
            1. Creates a CircuitBuilder instance: builder = CircuitBuilder()
            2. Sets title and global node (ground = "0")
            3. Defines any required .MODEL statements for active devices
            4. Adds all components with proper node connections
            5. Adds analysis directives
            6. Ends with: netlist = builder.netlist()

            IMPORTANT:
            - Do NOT add any import statements.
            - Ensure node names match the blueprint exactly.
            - Use proper SPICE value strings (e.g. "10k", "1u", "100n").
        """).strip()



# Module-level convenience function

def synthesize_circuit(blueprint: dict) -> SynthesisResult:
    synthesizer = SpecialistSynthesizer()
    return synthesizer.synthesize(blueprint)