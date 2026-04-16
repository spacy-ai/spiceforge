from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

from app.core.netlist_pipeline import (
    detect_analyses,
    extract_analysis_lines,
    prepare_netlist,
    validate_netlist_text,
)
from app.core.raw_parser import parse_results
from app.schema.simulation import AnalysisType, AnalysisResult, ErrorDetail, SimulationOptions


class NgspiceFailure(Exception):
    def __init__(
        self,
        detail: ErrorDetail,
        stdout: str | None = None,
        stderr: str | None = None,
        returncode: int | None = None,
    ) -> None:
        self.detail = detail
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(detail.message)


def validate_netlist(netlist: str) -> None:
    try:
        validate_netlist_text(netlist)
    except ValueError as exc:
        msg = str(exc)
        if "empty" in msg.lower():
            code = "NETLIST_EMPTY"
            hint = "Provide a valid SPICE netlist with at least one analysis command."
        elif "missing .end" in msg.lower():
            code = "NETLIST_MISSING_END"
            hint = "Add a trailing .end statement to the netlist."
        else:
            code = "ANALYSIS_NOT_FOUND"
            hint = "Include .op, .tran, .ac, .dc, .tf, .noise, or .pz."
        raise NgspiceFailure(
            ErrorDetail(code=code, message=msg, hint=hint)
        )


def run_ngspice_once(
    *, netlist: str, analysis_line: str, timeout_seconds: int
) -> tuple[str, str, Path, Path]:
    tmpdir = Path(tempfile.mkdtemp(prefix="spice_platform_"))
    netlist_path = tmpdir / "input.cir"
    log_path = tmpdir / "ngspice.log"
    raw_path = tmpdir / "circuit.raw"

    prepared_netlist = prepare_netlist(netlist, analysis_line)
    netlist_path.write_text(prepared_netlist, encoding="utf-8")

    process = subprocess.run(
        ["ngspice", "-b", "-r", str(raw_path), "-o", str(log_path), str(netlist_path)],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    stdout = process.stdout or ""
    stderr = process.stderr or ""
    if process.returncode != 0:
        raise NgspiceFailure(
            ErrorDetail(
                code="NGSPICE_FAILED",
                message="ngspice returned a non-zero exit code.",
                hint="Inspect stdout/stderr for details.",
            ),
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode,
        )

    if not raw_path.exists() or raw_path.stat().st_size == 0:
        raise NgspiceFailure(
            ErrorDetail(
                code="RAW_OUTPUT_MISSING",
                message="Simulation produced no raw output.",
                hint="Ensure analysis command is valid and netlist is solvable.",
            ),
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode,
        )

    return stdout, stderr, raw_path, tmpdir


def _extract_measurements(analysis: AnalysisType, parsed: dict) -> dict:
    if analysis == AnalysisType.ac:
        return {
            "bandwidth": {
                "f_cutoff_hz": parsed.get("f_3dB_hz"),
                "rolloff_db_per_decade": parsed.get("rolloff_rate_dB_per_decade"),
                "threshold_db": -3.0,
            }
        }
    if analysis == AnalysisType.tran:
        rise_s = parsed.get("rise_time_10_90_s")
        settling_s = parsed.get("settling_time_1pct_s")
        return {
            "transient": {
                "rise_time_us": rise_s * 1e6 if rise_s is not None else None,
                "settling_time_us": settling_s * 1e6 if settling_s is not None else None,
                "overshoot_pct": parsed.get("overshoot_pct"),
                "steady_state_V": parsed.get("steady_state_value"),
            }
        }
    return {}


def run_ngspice(
    netlist: str, options: SimulationOptions | None
) -> Tuple[List[AnalysisType], List[AnalysisResult], str, str]:
    validate_netlist(netlist)
    analyses = detect_analyses(netlist)

    if shutil.which("ngspice") is None:
        raise NgspiceFailure(
            ErrorDetail(
                code="NGSPICE_NOT_FOUND",
                message="ngspice binary not found.",
                hint="Install ngspice and ensure it is on PATH.",
            )
        )

    opts = options or SimulationOptions()
    timeout = opts.timeout_seconds
    preserve_artifacts = opts.preserve_artifacts

    per_analysis_lines = extract_analysis_lines(netlist)
    run_analyses: List[AnalysisType] = []
    run_results: List[AnalysisResult] = []
    stdout_parts: List[str] = []
    stderr_parts: List[str] = []

    for analysis in analyses:
        line = per_analysis_lines.get(analysis)
        if line is None:
            continue
        run_analyses.append(analysis)

        stdout, stderr, raw_path, tmpdir = run_ngspice_once(
            netlist=netlist,
            analysis_line=line,
            timeout_seconds=timeout,
        )
        try:
            parsed = parse_results(raw_path)
        finally:
            if not preserve_artifacts:
                shutil.rmtree(tmpdir, ignore_errors=True)

        stdout_parts.append(stdout)
        stderr_parts.append(stderr)
        run_results.append(
            AnalysisResult(
                analysis=analysis,
                data=parsed,
                measurements=_extract_measurements(analysis, parsed),
                warnings=parsed.get("warnings", []),
            )
        )

    merged_stdout = "\n".join(part.strip() for part in stdout_parts if part and part.strip())
    merged_stderr = "\n".join(part.strip() for part in stderr_parts if part and part.strip())
    return run_analyses, run_results, merged_stdout, merged_stderr


def parse_ngspice_output(
    analyses: List[AnalysisType], log_content: str
) -> List[AnalysisResult]:
    # Legacy compatibility hook; retained for callers that still import this symbol.
    _ = log_content
    return [AnalysisResult(analysis=analysis) for analysis in analyses]
