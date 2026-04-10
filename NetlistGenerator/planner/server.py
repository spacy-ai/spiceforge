# server endpoints
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from spacy.planner.planner import CircuitBlueprint, Planner

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# pydantic schemas

class CircuitDescriptionRequest(BaseModel):
    # /plan payload

    description: str = Field(..., description="Natural language circuit description")
    session_id: Optional[str] = Field(None, description="Optional session ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Design a two-stage CMOS amplifier with common-source first stage and common-drain output stage",
                "session_id": "session-abc-123",
            }
        }
    }


class RepairFeedbackRequest(BaseModel):
    # POST /plan/{circuit_id}/repair payload

    error_type: str = Field(
        ...,
        description="Category of error: convergence | syntax | floating_nodes | model | …",
    )
    message: str = Field(..., description="Human readable error message from simulator")
    error_details: Optional[Dict[str, Any]] = Field(
        None, description="Optional structured error context"
    )
    circuit_id: Optional[str] = Field(None, description="ID of the offending circuit")


class StoreNetlistRequest(BaseModel):
    # Payload for POST /store-netlist

    netlist: str = Field(..., description="Raw SPICE netlist string")


class ComponentOut(BaseModel):
    # A single component entry in  response

    component_type: str
    name: str
    nodes: List[str]
    parameters: Dict[str, Any]
    model: Optional[str]


class CircuitBlueprintResponse(BaseModel):
    # Unified response shape returned by both /plan and /plan/{id}/repair.
    # The `status` field distinguishes creation ("success") from repair ("repaired").

    circuit_id: str
    description: str
    input_nodes: List[str]
    output_nodes: List[str]
    ground_node: str
    components: List[ComponentOut]
    analyses: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    topology_notes: str
    design_decisions: List[str]
    status: str  # "success" or "repaired"


# 2. Serialisation helper Converts an internal CircuitBlueprint to CircuitBlueprintResponse

def blueprint_to_response(
    blueprint: CircuitBlueprint,
    status: str,
) -> CircuitBlueprintResponse:
    
    return CircuitBlueprintResponse(
        circuit_id=blueprint.circuit_id,
        description=blueprint.description,
        input_nodes=blueprint.input_nodes,
        output_nodes=blueprint.output_nodes,
        ground_node=blueprint.ground_node,
        components=[
            ComponentOut(
                component_type=c.component_type,
                name=c.name,
                nodes=c.nodes,
                parameters=c.parameters,
                model=c.model,
            )
            for c in blueprint.components
        ],
        analyses=blueprint.analyses,
        constraints=blueprint.constraints,
        topology_notes=blueprint.topology_notes,
        design_decisions=blueprint.design_decisions,
        status=status,
    )


# 3. PlannerService

class PlannerService:
    """
    orchestration layer between FastAPI routes and the Planner agent.
    """

    def __init__(self) -> None:
        self._planner = Planner()


    def _find_plan(self, circuit_id: str) -> CircuitBlueprint:
        """
        look for a circuitblueprint based on id, search most recent first
        """
        current = self._planner.state.current_plan
        if current and current.circuit_id == circuit_id:
            return current

        for plan in reversed(self._planner.state.previous_plans):
            if plan.circuit_id == circuit_id:
                return plan

        raise HTTPException(
            status_code=404,
            detail=f"Circuit '{circuit_id}' not found in current plan or history.",
        )


    def create_plan(self, request: CircuitDescriptionRequest) -> CircuitBlueprintResponse:
        """
        POST /plan
        forward description to planner by calling llm, Serialise the resulting blueprint and Return response.
        """
        logger.info("Creating plan - description=%.80s…", request.description)

        try:
            blueprint = self._planner.create_plan(request.description)
        except Exception as exc:
            logger.error("Plan creation failed: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        logger.info(
            "Plan created - circuit_id=%s components=%d",
            blueprint.circuit_id,
            len(blueprint.components),
        )
        return blueprint_to_response(blueprint, status="success")

    def repair_plan(
        self,
        circuit_id: str,
        feedback: RepairFeedbackRequest,
    ) -> CircuitBlueprintResponse:
        """
        POST /plan/{circuit_id}/repair
        look for the target blueprint - forward blueprint + structured feedback to Planner - serialise and return the repaired blueprint.
        """
        logger.info("Repairing plan - circuit_id=%s error_type=%s", circuit_id, feedback.error_type)

        # 1 resolve the blueprint (404 if not found)
        blueprint = self._find_plan(circuit_id)

        # 2 ask the LLM to fix it
        feedback_dict: Dict[str, Any] = {
            "error_type": feedback.error_type,
            "message": feedback.message,
            "error_details": feedback.error_details or {},
        }

        try:
            repaired = self._planner.repair_plan(blueprint, feedback_dict)
        except Exception as exc:
            logger.error("Plan repair failed: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        logger.info("Plan repaired | circuit_id=%s", repaired.circuit_id)
        return blueprint_to_response(repaired, status="repaired")

    def get_plan(self, circuit_id: str) -> Dict[str, Any]:
        """
        GET /plan/{circuit_id}
        Look for blueprint by ID - Return as plain dict
        """
        blueprint = self._find_plan(circuit_id)
        return asdict(blueprint)

    def get_history(self) -> Dict[str, Any]:
        """
        GET /history
        return a summary dict of all plans and netlists held in memory.
        """
        return self._planner.to_dict()

    def reset(self) -> Dict[str, str]:
        """
        POST /reset
          clear all planner state
        """
        self._planner.reset_state()
        logger.info("Planner state reset.")
        return {"status": "reset", "message": "Planner state cleared."}

    def store_netlist(self, request: StoreNetlistRequest) -> Dict[str, Any]:
        """
        POST /store-netlist
          persist raw SPICE netlist string for use in future repairs.
        """
        self._planner.store_netlist(request.netlist)
        logger.info("Netlist stored - length=%d chars", len(request.netlist))
        return {"status": "stored", "netlist_length": len(request.netlist)}

    def health(self) -> Dict[str, Any]:
        """
        GET /health
          health check
        """
        return {"status": "healthy", "planner_state": self._planner.to_dict()}


# fastapi

app = FastAPI(
    title="SPACY Planner",
    version="1.0.0",
    description="Converts natural language circuit descriptions into structured blueprints.",
)

# Single shared planner instance
service = PlannerService()


@app.get("/", tags=["Meta"])
async def root():
    """Service info """
    return {
        "service": "SPACY Planner",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Meta"])
async def health_check():
    return service.health()


@app.post("/plan", response_model=CircuitBlueprintResponse, tags=["Planning"])
async def create_circuit_plan(request: CircuitDescriptionRequest):
    """
    Main entry point.
    Convert a natural-language description into a structured CircuitBlueprint ready for the Validator agent.
    """
    return service.create_plan(request)


@app.post(
    "/plan/{circuit_id}/repair",
    response_model=CircuitBlueprintResponse,
    tags=["Planning"],
)
async def repair_circuit_plan(circuit_id: str, feedback: RepairFeedbackRequest):
    """
    Repair loop entry point
    Called when the simulator returns an error. Feeds the blueprint and structured error back to the LLM to produce a corrected version.
    """
    return service.repair_plan(circuit_id, feedback)


@app.get("/plan/{circuit_id}", tags=["Planning"])
async def get_circuit_plan(circuit_id: str):
    """Fetch a specific plan by its circuit ID """
    return service.get_plan(circuit_id)


@app.get("/history", tags=["State"])
async def get_plan_history():
    """Return a summary of all plans and netlists held in memory."""
    return service.get_history()


@app.post("/reset", tags=["State"])
async def reset_planner():
    """wipe planner state"""
    return service.reset()


@app.post("/store-netlist", tags=["State"])
async def store_netlist(request: StoreNetlistRequest):
    """Persist a raw SPICE netlist for reference during future repair cycles."""
    return service.store_netlist(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")