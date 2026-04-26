from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.circuit_planner import Planner
from app.core.blueprint_validator import validate_circuit_blueprint, ValidationResult
from app.services.netlist_synthesizer import SpecialistSynthesizer

router = APIRouter(tags=["netlist generation"])


class GenerateNetlistRequest(BaseModel):
    prompt: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None


class GenerateNetlistResponse(BaseModel):
    success: bool
    netlist: str
    summary: Optional[str] = None
    python_code: Optional[str] = None
    error: Optional[str] = None


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
    try:
        planner = Planner(
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
        )

        blueprint = planner.create_plan(request.prompt)

        validation_result = validate_circuit_blueprint(
            {
                "circuit_id": blueprint.circuit_id,
                "description": blueprint.description,
                "input_nodes": blueprint.input_nodes,
                "output_nodes": blueprint.output_nodes,
                "ground_node": blueprint.ground_node,
                "components": [
                    {
                        "component_type": c.component_type,
                        "name": c.name,
                        "nodes": c.nodes,
                        "parameters": c.parameters,
                        "model": c.model,
                    }
                    for c in blueprint.components
                ],
                "analyses": blueprint.analyses,
                "constraints": blueprint.constraints,
                "topology_notes": blueprint.topology_notes,
                "design_decisions": blueprint.design_decisions,
            }
        )

        if not validation_result.is_valid:
            error_messages = [
                f"{i.category}: {i.message}" for i in validation_result.issues
            ]
            return GenerateNetlistResponse(
                success=False,
                netlist="",
                summary=None,
                error=f"Validation failed: {'; '.join(error_messages)}",
            )

        synthesizer = SpecialistSynthesizer(
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
        )

        result = synthesizer.synthesize(validation_result.validated_blueprint)

        return GenerateNetlistResponse(
            success=True,
            netlist=result.netlist or "",
            summary=getattr(blueprint, "summary", None),
            python_code=result.python_code,
            error=None,
        )

    except Exception as exc:
        return GenerateNetlistResponse(
            success=False,
            netlist="",
            summary=None,
            error=str(exc),
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