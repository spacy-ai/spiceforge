from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.core.blueprint_validator import validate_circuit_blueprint
from app.core.dependencies import get_db, get_optional_current_user
from app.models.pipeline_models import PipelineResult
from app.models.user import User
from app.services.pipeline_runner import run_pipeline_with_context

router = APIRouter(tags=["netlist generation"])
log = logging.getLogger(__name__)


class GenerateNetlistRequest(BaseModel):
    prompt: str
    circuit_id: int | None = None
    api_key: str | None = None
    api_base: str | None = None
    model: str | None = None
    run_simulation: bool = True


class GenerateNetlistResponse(BaseModel):
    success: bool
    circuit_id: int | None = None
    title: str | None = None
    netlist: str
    summary: str | None = None
    error: str | None = None
    blueprint: dict | None = None
    simulation: dict | None = None
    clarifications: list[str] = []
    intent: str | None = None
    changes_summary: str | None = None


class ValidateRequest(BaseModel):
    blueprint: dict


class ValidateResponse(BaseModel):
    is_valid: bool
    issues: list[dict]
    error: str | None = None


@router.get("/")
def root():
    return {"service": "Netlist Generation Service", "status": "ready"}


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.post("/generate-netlist", response_model=GenerateNetlistResponse)
def generate_netlist(
    request: GenerateNetlistRequest,
    db: DBSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return _pipeline_generate(request, db, current_user)


def _pipeline_generate(
    request: GenerateNetlistRequest,
    db: DBSession,
    current_user: User | None,
) -> GenerateNetlistResponse:
    try:
        run_result = run_pipeline_with_context(
            db,
            prompt=request.prompt,
            circuit_id=request.circuit_id,
            user_id=current_user.id if current_user else None,
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
            run_simulation=request.run_simulation,
        )

        result: PipelineResult = run_result.result

        netlist = ""
        if result.synthesis:
            netlist = result.synthesis.netlist

        sim_dict = None
        if result.simulation:
            sim_dict = {
                "success": result.simulation.success,
                "analyses": result.simulation.analyses,
                "results": result.simulation.results,
                "stdout": result.simulation.stdout[-2000:] if result.simulation.stdout else "",
                "stderr": result.simulation.stderr[-2000:] if result.simulation.stderr else "",
                "error": result.simulation.error,
                "convergence_failures": result.simulation.convergence_failures,
            }

        intent_str = result.intent.intent.value if result.intent else None

        return GenerateNetlistResponse(
            success=result.success,
            circuit_id=run_result.circuit_id,
            title=result.title or "",
            netlist=netlist,
            summary=result.summary or "",
            error=result.error,
            blueprint=result.blueprint,
            simulation=sim_dict,
            clarifications=result.clarifications,
            intent=intent_str,
            changes_summary=result.changes_summary,
        )

    except Exception as exc:
        log.warning("Pipeline generation failed: %s", exc)
        return GenerateNetlistResponse(
            success=False,
            netlist="",
            summary=None,
            error=str(exc),
            title=None,
        )


@router.post("/validate", response_model=ValidateResponse)
def validate_blueprint(request: ValidateRequest):
    try:
        result = validate_circuit_blueprint(request.blueprint)
        return ValidateResponse(
            is_valid=result.is_valid,
            issues=[
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                    "component_name": i.component_name,
                    "node": i.node,
                }
                for i in result.issues
            ],
            error=None,
        )
    except Exception as exc:
        return ValidateResponse(
            is_valid=False,
            issues=[],
            error=str(exc),
        )
