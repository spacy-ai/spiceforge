from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from spacy.validator import BlueprintValidator, ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentSpecInput(BaseModel):

    component_type: str = Field(
        ..., description="Type of component (resistor, capacitor, mosfet, etc.)"
    )
    name: str = Field(..., description="Component name (e.g., R1, C1, M1)")
    nodes: List[str] = Field(..., description="Node connections")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Component parameters"
    )
    model: Optional[str] = Field(None, description="Model name for device models")


class CircuitBlueprintInput(BaseModel):

    circuit_id: Optional[str] = Field(None, description="Unique circuit identifier")
    description: Optional[str] = Field(None, description="Natural language description")
    input_nodes: List[str] = Field(default_factory=list, description="Input nodes")
    output_nodes: List[str] = Field(default_factory=list, description="Output nodes")
    ground_node: str = Field("0", description="Ground node reference")
    components: List[ComponentSpecInput] = Field(
        default_factory=list, description="Circuit components"
    )
    analyses: List[Dict[str, Any]] = Field(
        default_factory=list, description="Analysis directives"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Design constraints"
    )
    topology_notes: str = Field("", description="Topology notes")
    design_decisions: List[str] = Field(
        default_factory=list, description="Design decisions"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "circuit_id": "common_source_amp",
                "description": "Single-stage common-source amplifier with resistive load",
                "ground_node": "0",
                "components": [
                    {
                        "component_type": "resistor",
                        "name": "R1",
                        "nodes": ["Vout", "Vdd"],
                        "parameters": {"resistance": 10000},
                    },
                    {
                        "component_type": "mosfet",
                        "name": "M1",
                        "nodes": ["Vout", "Vin", "0", "0"],
                        "parameters": {"w": 50e-6, "l": 1e-6, "model": "nmos_model"},
                    },
                    {
                        "component_type": "voltage_source",
                        "name": "Vdd",
                        "nodes": ["Vdd", "0"],
                        "parameters": {"dc_value": 5.0},
                    },
                ],
                "analyses": [{"type": "op", "parameters": {}}],
            }
        }
    }


class ValidationIssueOutput(BaseModel):

    severity: str = Field(..., description="Error or warning")
    category: str = Field(..., description="Issue category")
    message: str = Field(..., description="Human-readable message")
    component_name: Optional[str] = Field(None, description="Related component name")
    node: Optional[str] = Field(None, description="Related node")


class ValidationResponse(BaseModel):

    is_valid: bool = Field(
        ..., description="True if blueprint passes all validation checks"
    )
    issues: List[ValidationIssueOutput] = Field(
        default_factory=list, description="Validation issues found"
    )
    validated_blueprint: Optional[Dict[str, Any]] = Field(
        None, description="Validated blueprint if valid"
    )


class ValidatorService:

    def __init__(self) -> None:
        self._validator = BlueprintValidator()

    def validate(self, blueprint: dict) -> ValidationResponse:
        """Validate a circuit blueprint."""
        logger.info("Validating blueprint: %s", blueprint.get("circuit_id", "unknown"))

        result = self._validator.validate(blueprint)

        logger.info(
            "Validation complete: is_valid=%s, issues=%d",
            result.is_valid,
            len(result.issues),
        )

        return ValidationResponse(
            is_valid=result.is_valid,
            issues=[
                ValidationIssueOutput(
                    severity=i.severity.value,
                    category=i.category,
                    message=i.message,
                    component_name=i.component_name,
                    node=i.node,
                )
                for i in result.issues
            ],
            validated_blueprint=result.validated_blueprint,
        )


app = FastAPI(
    title="SPACY Validator",
    version="1.0.0",
    description="Deterministic structural and syntax validation for circuit blueprints.",
)

service = ValidatorService()


@app.get("/", tags=["Meta"])
async def root():
    """Service info."""
    return {
        "service": "SPACY Validator",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Meta"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post(
    "/validate",
    response_model=ValidationResponse,
    tags=["Validation"],
)
async def validate_blueprint(blueprint: CircuitBlueprintInput):
   
    return service.validate(blueprint.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
