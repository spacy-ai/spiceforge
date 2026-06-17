from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.blueprint_validator import validate_circuit_blueprint
from app.models.pipeline_models import PipelineResult, SynthesisResult
from app.services.netlist_generation_pipeline import NetlistGenerationPipeline

router = APIRouter(tags=["netlist generation"])


class GenerateNetlistRequest(BaseModel):
    prompt: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    run_simulation: bool = True


class GenerateNetlistResponse(BaseModel):
    success: bool
    title: Optional[str] = None
    netlist: str
    summary: Optional[str] = None
    python_code: Optional[str] = None
    error: Optional[str] = None
    blueprint: Optional[dict] = None
    simulation: Optional[dict] = None
    clarifications: list[str] = []


class ValidateRequest(BaseModel):
    blueprint: dict


class ValidateResponse(BaseModel):
    is_valid: bool
    issues: list[dict]
    error: Optional[str] = None


@router.get("/")
def root():
    return {"service": "Netlist Generation Service", "status": "ready"}


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.post("/generate-netlist", response_model=GenerateNetlistResponse)
def generate_netlist(request: GenerateNetlistRequest):
    return _pipeline_generate(request)


def _pipeline_generate(request: GenerateNetlistRequest) -> GenerateNetlistResponse:
    try:
        pipeline = NetlistGenerationPipeline(
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
        )

        result: PipelineResult = pipeline.run(
            prompt=request.prompt,
            run_simulation=request.run_simulation,
        )

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

        return GenerateNetlistResponse(
            success=result.success,
            title=result.title or "",
            netlist=netlist,
            summary=result.summary or "",
            python_code=None,
            error=result.error,
            blueprint=result.blueprint,
            simulation=sim_dict,
            clarifications=result.clarifications,
        )

    except Exception as exc:
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