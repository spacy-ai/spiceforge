from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...services.ngspice import NgspiceFailure, run_ngspice
from ...schema import ErrorDetail, SimulationRequest, SimulationResponse

router = APIRouter(tags=["simulation"])


@router.post("/simulate", response_model=SimulationResponse)
async def simulate(payload: SimulationRequest) -> SimulationResponse:
    try:
        analyses, results, stdout, stderr = run_ngspice(
            payload.netlist, payload.options
        )
    except NgspiceFailure as exc:
        detail = exc.detail
        return SimulationResponse(
            status="error",
            analyses=[],
            results=[],
            stdout=exc.stdout,
            stderr=exc.stderr,
            returncode=exc.returncode,
            error=detail,
        )
    except Exception as exc:
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            hint=str(exc),
        )
        raise HTTPException(status_code=500, detail=detail.model_dump())

    return SimulationResponse(
        status="success",
        analyses=analyses,
        results=results,
        stdout=stdout,
        stderr=stderr,
        returncode=0,
        error=None,
    )
