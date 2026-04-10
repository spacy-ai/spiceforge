from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

from app.core.schema import AnalysisType, AnalysisResult, ErrorDetail, SimulationOptions

_ANALYSIS_PATTERNS = [
    (AnalysisType.op, re.compile(r"^\.op\b", re.IGNORECASE)),
    (AnalysisType.ac, re.compile(r"^\.ac\b", re.IGNORECASE)),
    (AnalysisType.dc, re.compile(r"^\.dc\b", re.IGNORECASE)),
    (AnalysisType.tran, re.compile(r"^\.tran\b", re.IGNORECASE)),
    (AnalysisType.tf, re.compile(r"^\.tf\b", re.IGNORECASE)),
    (AnalysisType.noise, re.compile(r"^\.noise\b", re.IGNORECASE)),
    (AnalysisType.pz, re.compile(r"^\.pz\b", re.IGNORECASE)),
]


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


def detect_analyses(netlist: str) -> List[AnalysisType]:
    analyses: List[AnalysisType] = []
    for line in netlist.splitlines():
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        for analysis, pattern in _ANALYSIS_PATTERNS:
            if pattern.search(line):
                analyses.append(analysis)
    return analyses


def validate_netlist(netlist: str) -> None:
    if not netlist.strip():
        raise NgspiceFailure(
            ErrorDetail(
                code="NETLIST_EMPTY",
                message="Netlist is empty.",
                hint="Provide a valid SPICE netlist with at least one analysis command.",
            )
        )
    if ".end" not in netlist.lower():
        raise NgspiceFailure(
            ErrorDetail(
                code="NETLIST_MISSING_END",
                message="Netlist missing .end line.",
                hint="Add a trailing .end statement to the netlist.",
            )
        )

    analyses = detect_analyses(netlist)
    if not analyses:
        raise NgspiceFailure(
            ErrorDetail(
                code="ANALYSIS_NOT_FOUND",
                message="No analysis command found in netlist.",
                hint="Include .op, .tran, .ac, .dc, .tf, .noise, or .pz.",
            )
        )


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

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        netlist_path = tmp_path / "input.cir"
        log_path = tmp_path / "ngspice.log"

        netlist_path.write_text(netlist, encoding="utf-8")

        process = subprocess.run(
            ["ngspice", "-b", "-o", str(log_path), str(netlist_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
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

        log_content = ""
        if log_path.exists():
            log_content = log_path.read_text(encoding="utf-8", errors="ignore")

        results = parse_ngspice_output(analyses, log_content)
        merged_stdout = "\n".join(filter(None, [stdout.strip(), log_content.strip()]))
        return analyses, results, merged_stdout, stderr


def parse_ngspice_output(
    analyses: List[AnalysisType], log_content: str
) -> List[AnalysisResult]:
    results: List[AnalysisResult] = []
    for analysis in analyses:
        results.append(AnalysisResult(analysis=analysis))
    return results
