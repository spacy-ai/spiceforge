from __future__ import annotations

from app.core.netlist_builder import CircuitBuilder


class AnalysisRenderer:
    @staticmethod
    def render(builder: CircuitBuilder, analysis: dict) -> None:
        atype = analysis.get("type", "").lower()
        params = analysis.get("parameters", {})

        if atype == "ac":
            builder.ac_analysis(
                start_freq=float(params.get("start_freq", 1)),
                stop_freq=float(params.get("stop_freq", 1e6)),
                num_points=int(params.get("num_points", 100)),
            )
        elif atype == "transient":
            builder.transient(
                tstart=float(params.get("tstart", 0)),
                tstop=float(params.get("tstop", 1e-3)),
                tstep=float(params.get("tstep", 1e-6)),
            )
        elif atype == "dc" or atype == "dc_sweep":
            if atype == "dc_sweep":
                sv = params.get("sweep_variable", params.get("source", "V1"))
                start = float(params.get("start", 0))
                stop = float(params.get("stop", 5))
                step = float(params.get("step", 0.1))
            else:
                sv = params.get("source", "V1")
                start = float(params.get("start", 0))
                stop = float(params.get("stop", 5))
                step = float(params.get("step", 0.1))
            builder.dc_sweep(sv, start, stop, step)
        elif atype == "op":
            builder.operating_point()
