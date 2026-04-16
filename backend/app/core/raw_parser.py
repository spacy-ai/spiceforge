from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from spicelib import RawRead

_SWEEP_VARIABLES = frozenset({"frequency", "time", "v-sweep", "i-sweep", "temp-sweep"})


def _sanitize_array(arr: np.ndarray, label: str) -> tuple[np.ndarray, list[str]]:
    warnings: list[str] = []
    nan_mask = np.isnan(arr)
    if np.any(nan_mask):
        count = int(np.sum(nan_mask))
        warnings.append(f"NaN detected in {label}: {count} value(s) replaced with 0.0")
        arr = np.where(nan_mask, 0.0, arr)
    return arr, warnings


def detect_analysis_type(raw_path: str | Path) -> str:
    raw = RawRead(str(raw_path), dialect="ngspice")
    return raw.get_plot_name()


def _select_output_trace(trace_names: list[str]) -> str:
    if not trace_names:
        raise ValueError("No traces available")

    skip = {"v(in)", "v(v1)"}
    lower_names = [name.lower() for name in trace_names]

    if "v(out)" in lower_names:
        return trace_names[lower_names.index("v(out)")]

    for index, name in enumerate(lower_names):
        if name.startswith("v(") and name.endswith(")") and name not in skip:
            return trace_names[index]

    candidates = [trace for trace in trace_names if trace.lower() not in _SWEEP_VARIABLES]
    if not candidates:
        raise ValueError("No output traces found (only sweep variables present)")

    return candidates[0]


def parse_ac(raw_path: str | Path) -> dict[str, Any]:
    warnings: list[str] = []
    raw = RawRead(str(raw_path), dialect="ngspice")
    trace_names = raw.get_trace_names()

    output_trace = _select_output_trace(trace_names)
    freqs = np.real(raw.get_trace("frequency").get_wave(0))
    if len(freqs) == 0:
        raise ValueError("Empty frequency data")

    freqs, freq_warnings = _sanitize_array(freqs, "frequency")
    warnings.extend(freq_warnings)

    data = raw.get_trace(output_trace).get_wave(0)
    abs_data = np.abs(data)
    abs_data, mag_warnings = _sanitize_array(abs_data, "magnitude")
    warnings.extend(mag_warnings)

    mag_db = 20 * np.log10(abs_data + 1e-20)
    phase = np.angle(data, deg=True)

    gain_dc_db = float(mag_db[0])

    peak_idx = int(np.argmax(mag_db))
    peak_gain_db = float(mag_db[peak_idx])
    peak_gain_freq = float(freqs[peak_idx])

    threshold = gain_dc_db - 3.0
    f_3db = None
    phase_at_f3db = None
    rolloff_rate = None

    below = np.where(mag_db < threshold)[0]
    if len(below) > 0:
        idx = below[0]
        if idx > 0:
            f_3db = float(np.interp(threshold, [mag_db[idx], mag_db[idx - 1]], [freqs[idx], freqs[idx - 1]]))
            phase_at_f3db = float(np.interp(f_3db, [freqs[idx - 1], freqs[idx]], [phase[idx - 1], phase[idx]]))
            f_decade = f_3db * 10
            if f_decade <= freqs[-1]:
                gain_at_decade = float(np.interp(f_decade, freqs, mag_db))
                rolloff_rate = gain_at_decade - float(np.interp(f_3db, freqs, mag_db))
        else:
            f_3db = float(freqs[0])
            phase_at_f3db = float(phase[0])

    result: Dict[str, Any] = {
        "analysis_type": "AC Analysis",
        "traces": list(trace_names),
        "f_3dB_hz": f_3db,
        "gain_dc_dB": gain_dc_db,
        "rolloff_rate_dB_per_decade": rolloff_rate,
        "phase_at_f3dB_deg": phase_at_f3db,
        "peak_gain_dB": peak_gain_db,
        "peak_gain_freq_hz": peak_gain_freq,
        "num_points": len(freqs),
        "freq_range": [float(freqs[0]), float(freqs[-1])],
    }
    if warnings:
        result["warnings"] = warnings
    return result


def parse_transient(raw_path: str | Path) -> dict[str, Any]:
    warnings: list[str] = []
    raw = RawRead(str(raw_path), dialect="ngspice")
    trace_names = raw.get_trace_names()

    output_trace = _select_output_trace(trace_names)
    time = np.real(raw.get_trace("time").get_wave(0))
    voltage = np.real(raw.get_trace(output_trace).get_wave(0))

    if len(time) == 0 or len(voltage) == 0:
        raise ValueError("Empty time or voltage data")

    time, time_warnings = _sanitize_array(time, "time")
    warnings.extend(time_warnings)
    voltage, voltage_warnings = _sanitize_array(voltage, "voltage")
    warnings.extend(voltage_warnings)

    n_last = max(1, len(voltage) // 10)
    steady_state = float(np.mean(voltage[-n_last:]))
    peak_value = float(np.max(voltage))

    rise_time = None
    if steady_state != 0:
        thresh_10 = 0.1 * steady_state
        thresh_90 = 0.9 * steady_state
        cross_10 = np.where(voltage >= thresh_10)[0]
        cross_90 = np.where(voltage >= thresh_90)[0]
        if len(cross_10) > 0 and len(cross_90) > 0:
            rise_time = float(time[cross_90[0]] - time[cross_10[0]])

    overshoot = None
    if steady_state > 0:
        overshoot = float((peak_value - steady_state) / steady_state * 100)

    settling_time = None
    if steady_state != 0:
        tolerance = abs(steady_state) * 0.01
        within = np.abs(voltage - steady_state) <= tolerance
        for index in range(len(within) - 1, -1, -1):
            if not within[index]:
                if index + 1 < len(time):
                    settling_time = float(time[index + 1])
                break

    result: Dict[str, Any] = {
        "analysis_type": "Transient Analysis",
        "traces": list(trace_names),
        "steady_state_value": steady_state,
        "peak_value": peak_value,
        "rise_time_10_90_s": rise_time,
        "overshoot_pct": overshoot,
        "settling_time_1pct_s": settling_time,
        "num_points": len(time),
        "time_range": [float(time[0]), float(time[-1])],
    }
    if warnings:
        result["warnings"] = warnings
    return result


def parse_dc_op(raw_path: str | Path) -> dict[str, Any]:
    warnings: List[str] = []
    raw = RawRead(str(raw_path), dialect="ngspice")
    trace_names = raw.get_trace_names()
    if not trace_names:
        raise ValueError("No traces found in raw file")

    nodes: Dict[str, float] = {}
    for name in trace_names:
        wave = raw.get_trace(name).get_wave(0)
        if len(wave) == 0:
            warnings.append(f"Empty wave data for trace '{name}'")
            continue
        value = float(wave[0])
        if np.isnan(value):
            warnings.append(f"NaN value for trace '{name}', replaced with 0.0")
            value = 0.0
        nodes[name] = value

    result: Dict[str, Any] = {
        "analysis_type": "Operating Point",
        "nodes": nodes,
        "num_nodes": len(nodes),
    }
    if warnings:
        result["warnings"] = warnings
    return result


def parse_results(raw_path: str | Path) -> dict[str, Any]:
    analysis = detect_analysis_type(raw_path)
    if "AC" in analysis:
        return parse_ac(raw_path)
    if "Transient" in analysis:
        return parse_transient(raw_path)
    if "Operating Point" in analysis:
        return parse_dc_op(raw_path)
    raise ValueError(f"Unknown analysis type: {analysis}")


def read_ac_at_frequency(raw_path: str | Path, frequency_hz: float) -> dict[str, Any]:
    raw = RawRead(str(raw_path), dialect="ngspice")
    trace_names = raw.get_trace_names()
    output_trace = _select_output_trace(trace_names)
    freqs = np.real(raw.get_trace("frequency").get_wave(0))

    if len(freqs) < 2:
        raise ValueError("Insufficient frequency data for interpolation")
    if frequency_hz < freqs[0] or frequency_hz > freqs[-1]:
        raise ValueError(
            f"Frequency {frequency_hz} Hz is outside simulated range [{float(freqs[0])}, {float(freqs[-1])}] Hz"
        )

    data = raw.get_trace(output_trace).get_wave(0)
    abs_data = np.abs(data)
    mag_db = 20 * np.log10(abs_data + 1e-20)
    phase = np.angle(data, deg=True)

    return {
        "gain_db": float(np.interp(frequency_hz, freqs, mag_db)),
        "phase_deg": float(np.interp(frequency_hz, freqs, phase)),
    }


def read_ac_bandwidth(raw_path: str | Path, threshold_db: float) -> dict[str, Any]:
    raw = RawRead(str(raw_path), dialect="ngspice")
    trace_names = raw.get_trace_names()
    output_trace = _select_output_trace(trace_names)

    freqs = np.real(raw.get_trace("frequency").get_wave(0))
    if len(freqs) == 0:
        raise ValueError("Empty frequency data")

    data = raw.get_trace(output_trace).get_wave(0)
    mag_db = 20 * np.log10(np.abs(data) + 1e-20)

    gain_dc_db = float(mag_db[0])
    target = gain_dc_db + threshold_db

    f_cutoff = None
    rolloff_rate = None

    below = np.where(mag_db < target)[0]
    if len(below) > 0:
        idx = below[0]
        if idx > 0:
            f_cutoff = float(np.interp(target, [mag_db[idx], mag_db[idx - 1]], [freqs[idx], freqs[idx - 1]]))
            f_decade = f_cutoff * 10
            if f_decade <= freqs[-1]:
                gain_at_decade = float(np.interp(f_decade, freqs, mag_db))
                rolloff_rate = gain_at_decade - float(np.interp(f_cutoff, freqs, mag_db))
        else:
            f_cutoff = float(freqs[0])

    return {
        "f_cutoff_hz": f_cutoff,
        "rolloff_db_per_decade": rolloff_rate,
    }
