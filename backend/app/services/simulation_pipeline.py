from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.raw_parser import parse_results, read_ac_at_frequency, read_ac_bandwidth
from app.core.spice_values import parse_spice_value
from app.schema.simulation import AnalysisType
from app.services.ngspice import run_ngspice_once

_SOURCE_DC_RE = re.compile(
    r"^\s*(v\w+)\s+\S+\s+\S+\s+(?:dc\s+)?(\S+)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class AnalysisRun:
    analysis: AnalysisType
    analysis_line: str
    raw_path: Path
    result: dict[str, Any]
    netlist: str
    stdout: str
    stderr: str


def run_analysis_with_line(
    *,
    netlist: str,
    analysis: AnalysisType,
    analysis_line: str,
    timeout_seconds: int,
) -> AnalysisRun:
    stdout, stderr, raw_path, _tmpdir = run_ngspice_once(
        netlist=netlist,
        analysis_line=analysis_line,
        timeout_seconds=timeout_seconds,
    )
    result = parse_results(raw_path)
    return AnalysisRun(
        analysis=analysis,
        analysis_line=analysis_line,
        raw_path=raw_path,
        result=result,
        netlist=netlist,
        stdout=stdout,
        stderr=stderr,
    )


def run_ac_analysis(
    *,
    netlist: str,
    start_freq: float = 1.0,
    stop_freq: float = 1e6,
    points_per_decade: int = 10,
    timeout_seconds: int = 20,
) -> AnalysisRun:
    points_per_decade = int(points_per_decade)
    start_freq = float(start_freq)
    stop_freq = float(stop_freq)

    if not 1 <= points_per_decade <= 1000:
        raise ValueError("points_per_decade must be between 1 and 1000")
    if start_freq <= 0:
        raise ValueError("start_freq must be > 0")
    if stop_freq <= start_freq:
        raise ValueError("stop_freq must be > start_freq")

    analysis_line = f".ac dec {points_per_decade} {start_freq} {stop_freq}"
    return run_analysis_with_line(
        netlist=netlist,
        analysis=AnalysisType.ac,
        analysis_line=analysis_line,
        timeout_seconds=timeout_seconds,
    )


def run_transient(
    *,
    netlist: str,
    stop_time: float,
    step_time: float,
    startup_time: float | None = None,
    timeout_seconds: int = 20,
) -> AnalysisRun:
    stop_time = float(stop_time)
    step_time = float(step_time)
    if startup_time is not None:
        startup_time = float(startup_time)

    if step_time <= 0:
        raise ValueError("step_time must be > 0")
    if stop_time <= 0:
        raise ValueError("stop_time must be > 0")
    if stop_time / step_time > 1_000_000:
        raise ValueError("stop_time/step_time exceeds 1,000,000 steps")

    if startup_time is not None:
        analysis_line = f".tran {step_time} {stop_time} {startup_time}"
    else:
        analysis_line = f".tran {step_time} {stop_time}"

    return run_analysis_with_line(
        netlist=netlist,
        analysis=AnalysisType.tran,
        analysis_line=analysis_line,
        timeout_seconds=timeout_seconds,
    )


def run_dc_op(*, netlist: str, timeout_seconds: int = 20) -> AnalysisRun:
    return run_analysis_with_line(
        netlist=netlist,
        analysis=AnalysisType.op,
        analysis_line=".op",
        timeout_seconds=timeout_seconds,
    )


def _require_analysis_result(run: AnalysisRun, analysis_type: str) -> dict[str, Any]:
    result = run.result
    if result.get("analysis_type") != analysis_type:
        raise ValueError(
            f"Expected {analysis_type} results but found '{result.get('analysis_type')}'"
        )
    return result


def measure_bandwidth(run: AnalysisRun, threshold_db: float = -3.0) -> dict[str, Any]:
    if threshold_db >= 0:
        raise ValueError("threshold_db must be negative")

    result = _require_analysis_result(run, "AC Analysis")
    if threshold_db == -3.0:
        return {
            "f_cutoff_hz": result.get("f_3dB_hz"),
            "rolloff_db_per_decade": result.get("rolloff_rate_dB_per_decade"),
            "threshold_db": threshold_db,
        }

    bw = read_ac_bandwidth(run.raw_path, threshold_db)
    return {
        "f_cutoff_hz": bw.get("f_cutoff_hz"),
        "rolloff_db_per_decade": bw.get("rolloff_db_per_decade"),
        "threshold_db": threshold_db,
    }


def measure_gain(run: AnalysisRun, frequency_hz: float) -> dict[str, Any]:
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")

    _require_analysis_result(run, "AC Analysis")
    data = read_ac_at_frequency(run.raw_path, frequency_hz)
    return {
        "frequency_hz": frequency_hz,
        "gain_db": data["gain_db"],
        "phase_deg": data["phase_deg"],
    }


def measure_dc(run: AnalysisRun, node_name: str) -> dict[str, Any]:
    result = _require_analysis_result(run, "Operating Point")
    nodes = result.get("nodes", {})

    if node_name in nodes:
        return {"node_name": node_name, "voltage_V": nodes[node_name]}

    for key, value in nodes.items():
        if key.lower() == node_name.lower():
            return {"node_name": key, "voltage_V": value}

    raise ValueError(
        f"Node '{node_name}' not found. Available nodes: {list(nodes.keys())}"
    )


def measure_transient(run: AnalysisRun) -> dict[str, Any]:
    result = _require_analysis_result(run, "Transient Analysis")
    rise_s = result.get("rise_time_10_90_s")
    settling_s = result.get("settling_time_1pct_s")
    return {
        "rise_time_us": rise_s * 1e6 if rise_s is not None else None,
        "settling_time_us": settling_s * 1e6 if settling_s is not None else None,
        "overshoot_pct": result.get("overshoot_pct"),
        "steady_state_V": result.get("steady_state_value"),
    }


def _get_source_voltage(netlist: str, source_name: str) -> float | None:
    for match in _SOURCE_DC_RE.finditer(netlist):
        if match.group(1).lower() == source_name.lower():
            try:
                return parse_spice_value(match.group(2))
            except ValueError:
                return None
    return None


def measure_power(run: AnalysisRun) -> dict[str, Any]:
    result = _require_analysis_result(run, "Operating Point")
    nodes = result.get("nodes", {})

    per_source: dict[str, dict[str, float]] = {}
    total_power = 0.0

    for key, current in nodes.items():
        source_name = None
        if key.startswith("i(") and key.endswith(")"):
            source_name = key[2:-1]
        elif key.endswith("#branch"):
            source_name = key[: -len("#branch")]

        if source_name is None:
            continue

        voltage = _get_source_voltage(run.netlist, source_name)
        if voltage is None:
            continue

        power_w = -voltage * current
        per_source[source_name] = {
            "current_A": current,
            "voltage_V": voltage,
            "power_mW": power_w * 1e3,
        }
        total_power += power_w

    return {
        "total_power_mW": total_power * 1e3,
        "per_source": per_source,
    }
