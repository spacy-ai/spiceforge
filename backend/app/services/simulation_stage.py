from __future__ import annotations

import shutil

from app.core.netlist_pipeline import detect_analyses, extract_analysis_lines
from app.models.pipeline_models import (
    SimulationDiagnostic,
    SimulationResult,
)
from app.schema.simulation import AnalysisType


class SimulationStage:
    def run(self, netlist: str, timeout_seconds: int = 30) -> SimulationResult:
        from app.services.ngspice import NgspiceFailure, run_ngspice_once
        if not netlist or not netlist.strip():
            return SimulationResult(
                success=False,
                error="Empty netlist",
                diagnostics=[SimulationDiagnostic("error", "Empty netlist", "error")],
            )

        if shutil.which("ngspice") is None:
            return SimulationResult(
                success=False,
                error="ngspice binary not found. Install ngspice and ensure it is on PATH.",
                diagnostics=[SimulationDiagnostic("error", "ngspice not found", "error")],
            )

        try:
            analyses = detect_analyses(netlist)
        except Exception as exc:
            return SimulationResult(
                success=False,
                error=f"Failed to detect analyses: {exc}",
                diagnostics=[SimulationDiagnostic("error", str(exc), "error")],
            )

        if not analyses:
            return SimulationResult(
                success=False,
                error="No SPICE analyses found in netlist (.ac, .tran, .op, etc.)",
                diagnostics=[SimulationDiagnostic("error", "No analysis directives", "error")],
            )

        per_analysis_lines = extract_analysis_lines(netlist)
        all_results: list[dict] = []
        all_stdout: list[str] = []
        all_stderr: list[str] = []
        diagnostics: list[SimulationDiagnostic] = []
        convergence_failures: list[str] = []
        has_failure = False

        for analysis in analyses:
            line = per_analysis_lines.get(analysis)
            if line is None:
                diagnostics.append(
                    SimulationDiagnostic("warning", f"No line found for {analysis}")
                )
                continue

            try:
                stdout, stderr, raw_path, tmpdir = run_ngspice_once(
                    netlist=netlist,
                    analysis_line=line,
                    timeout_seconds=timeout_seconds,
                )
            except NgspiceFailure as exc:
                has_failure = True
                msg = f"Simulation failed for {analysis.value}: {exc.detail.message}"
                diagnostics.append(SimulationDiagnostic("error", msg, "error"))
                all_stderr.append(exc.stderr or "")
                all_stdout.append(exc.stdout or "")
                if "convergence" in str(exc).lower() or "singular" in str(exc).lower():
                    convergence_failures.append(f"{analysis.value}: {exc.detail.message}")
                continue
            except Exception as exc:
                has_failure = True
                msg = f"Unexpected error during {analysis.value}: {exc}"
                diagnostics.append(SimulationDiagnostic("error", msg, "error"))
                continue

            try:
                from app.core.raw_parser import parse_results
                parsed = parse_results(raw_path)
                result_entry = {
                    "analysis": analysis.value,
                    "data": parsed,
                }
                all_results.append(result_entry)
                all_stdout.append(stdout)
                all_stderr.append(stderr)

                if parsed.get("warnings"):
                    for w in parsed["warnings"]:
                        diagnostics.append(
                            SimulationDiagnostic("warning", str(w), "warning")
                        )
            except Exception as exc:
                diagnostics.append(
                    SimulationDiagnostic(
                        "error", f"Failed to parse results for {analysis.value}: {exc}", "error"
                    )
                )
                has_failure = True
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

        merged_stdout = "\n".join(s.strip() for s in all_stdout if s and s.strip())
        merged_stderr = "\n".join(s.strip() for s in all_stderr if s and s.strip())

        return SimulationResult(
            success=not has_failure and len(all_results) > 0,
            analyses=[a.value for a in analyses],
            results=all_results,
            stdout=merged_stdout,
            stderr=merged_stderr,
            error=None if not has_failure else "One or more analyses failed",
            diagnostics=diagnostics,
            convergence_failures=convergence_failures,
        )


def run_simulation_stage(netlist: str, timeout_seconds: int = 30) -> SimulationResult:
    return SimulationStage().run(netlist, timeout_seconds)
