from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schema.simulation import (
    AnalysisType,
    ErrorDetail,
    MeasureBandwidthRequest,
    MeasureDcRequest,
    MeasureGainRequest,
    MeasurementResponse,
    MeasurePowerRequest,
    MeasureTransientRequest,
)
from app.services.ngspice import NgspiceFailure
from app.services.simulation_pipeline import (
    measure_bandwidth,
    measure_dc,
    measure_gain,
    measure_power,
    measure_transient,
    run_ac_analysis,
    run_dc_op,
    run_transient,
)

router = APIRouter(tags=["measure"])

def _measurement_success(
    *,
    analysis: AnalysisType,
    measurement: dict,
    stdout: str,
    stderr: str,
) -> MeasurementResponse:
    return MeasurementResponse(
        status="success",
        analysis=analysis,
        measurement=measurement,
        stdout=stdout,
        stderr=stderr,
        returncode=0,
        error=None,
    )


def _measurement_failure(
    *, analysis: AnalysisType, exc: NgspiceFailure
) -> MeasurementResponse:
    return MeasurementResponse(
        status="error",
        analysis=analysis,
        measurement={},
        stdout=exc.stdout,
        stderr=exc.stderr,
        returncode=exc.returncode,
        error=exc.detail,
    )


@router.post("/bandwidth", response_model=MeasurementResponse)
async def measure_bandwidth_endpoint(
    payload: MeasureBandwidthRequest,
) -> MeasurementResponse:
    try:
        run = run_ac_analysis(
            netlist=payload.netlist,
            start_freq=payload.start_freq,
            stop_freq=payload.stop_freq,
            points_per_decade=payload.points_per_decade,
            timeout_seconds=payload.timeout_seconds,
        )
        measurement = measure_bandwidth(run, threshold_db=payload.threshold_db)
    except NgspiceFailure as exc:
        return _measurement_failure(analysis=AnalysisType.ac, exc=exc)
    except ValueError as exc:
        detail = ErrorDetail(
            code="INVALID_MEASURE_REQUEST",
            message=str(exc),
            hint="Check measure request inputs and analysis parameters.",
        )
        raise HTTPException(status_code=400, detail=detail.model_dump())
    except Exception as exc:
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            hint=str(exc),
        )
        raise HTTPException(status_code=500, detail=detail.model_dump())

    return _measurement_success(
        analysis=AnalysisType.ac,
        measurement=measurement,
        stdout=run.stdout,
        stderr=run.stderr,
    )


@router.post("/gain", response_model=MeasurementResponse)
async def measure_gain_endpoint(payload: MeasureGainRequest) -> MeasurementResponse:
    try:
        run = run_ac_analysis(
            netlist=payload.netlist,
            start_freq=payload.start_freq,
            stop_freq=payload.stop_freq,
            points_per_decade=payload.points_per_decade,
            timeout_seconds=payload.timeout_seconds,
        )
        measurement = measure_gain(run, frequency_hz=payload.frequency_hz)
    except NgspiceFailure as exc:
        return _measurement_failure(analysis=AnalysisType.ac, exc=exc)
    except ValueError as exc:
        detail = ErrorDetail(
            code="INVALID_MEASURE_REQUEST",
            message=str(exc),
            hint="Check measure request inputs and analysis parameters.",
        )
        raise HTTPException(status_code=400, detail=detail.model_dump())
    except Exception as exc:
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            hint=str(exc),
        )
        raise HTTPException(status_code=500, detail=detail.model_dump())

    return _measurement_success(
        analysis=AnalysisType.ac,
        measurement=measurement,
        stdout=run.stdout,
        stderr=run.stderr,
    )


@router.post("/dc", response_model=MeasurementResponse)
async def measure_dc_endpoint(payload: MeasureDcRequest) -> MeasurementResponse:
    try:
        run = run_dc_op(
            netlist=payload.netlist,
            timeout_seconds=payload.timeout_seconds,
        )
        measurement = measure_dc(run, node_name=payload.node_name)
    except NgspiceFailure as exc:
        return _measurement_failure(analysis=AnalysisType.op, exc=exc)
    except ValueError as exc:
        detail = ErrorDetail(
            code="INVALID_MEASURE_REQUEST",
            message=str(exc),
            hint="Check measure request inputs and analysis parameters.",
        )
        raise HTTPException(status_code=400, detail=detail.model_dump())
    except Exception as exc:
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            hint=str(exc),
        )
        raise HTTPException(status_code=500, detail=detail.model_dump())

    return _measurement_success(
        analysis=AnalysisType.op,
        measurement=measurement,
        stdout=run.stdout,
        stderr=run.stderr,
    )


@router.post("/transient", response_model=MeasurementResponse)
async def measure_transient_endpoint(
    payload: MeasureTransientRequest,
) -> MeasurementResponse:
    try:
        run = run_transient(
            netlist=payload.netlist,
            stop_time=payload.stop_time,
            step_time=payload.step_time,
            startup_time=payload.startup_time,
            timeout_seconds=payload.timeout_seconds,
        )
        measurement = measure_transient(run)
    except NgspiceFailure as exc:
        return _measurement_failure(analysis=AnalysisType.tran, exc=exc)
    except ValueError as exc:
        detail = ErrorDetail(
            code="INVALID_MEASURE_REQUEST",
            message=str(exc),
            hint="Check measure request inputs and analysis parameters.",
        )
        raise HTTPException(status_code=400, detail=detail.model_dump())
    except Exception as exc:
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            hint=str(exc),
        )
        raise HTTPException(status_code=500, detail=detail.model_dump())

    return _measurement_success(
        analysis=AnalysisType.tran,
        measurement=measurement,
        stdout=run.stdout,
        stderr=run.stderr,
    )


@router.post("/power", response_model=MeasurementResponse)
async def measure_power_endpoint(payload: MeasurePowerRequest) -> MeasurementResponse:
    try:
        run = run_dc_op(
            netlist=payload.netlist,
            timeout_seconds=payload.timeout_seconds,
        )
        measurement = measure_power(run)
    except NgspiceFailure as exc:
        return _measurement_failure(analysis=AnalysisType.op, exc=exc)
    except ValueError as exc:
        detail = ErrorDetail(
            code="INVALID_MEASURE_REQUEST",
            message=str(exc),
            hint="Check measure request inputs and analysis parameters.",
        )
        raise HTTPException(status_code=400, detail=detail.model_dump())
    except Exception as exc:
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            hint=str(exc),
        )
        raise HTTPException(status_code=500, detail=detail.model_dump())

    return _measurement_success(
        analysis=AnalysisType.op,
        measurement=measurement,
        stdout=run.stdout,
        stderr=run.stderr,
    )

