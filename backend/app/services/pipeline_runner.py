from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.models.circuit import Circuit
from app.models.pipeline_models import PipelineResult
from app.services.netlist_generation_pipeline import NetlistGenerationPipeline

log = logging.getLogger(__name__)


@dataclass
class PipelineRunResult:
    result: PipelineResult
    circuit_id: Optional[int] = None


def load_existing_blueprint(
    db: DBSession, circuit_id: int
) -> Optional[dict]:
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if circuit is None:
        return None
    if circuit.blueprint_json:
        return json.loads(circuit.blueprint_json)
    return None


def persist_circuit(
    db: DBSession,
    *,
    circuit_id: Optional[int],
    user_id: Optional[int],
    prompt: str,
    result: PipelineResult,
) -> Optional[int]:
    if not result.success or result.clarifications:
        return circuit_id

    blueprint = result.blueprint or {}
    netlist = result.synthesis.netlist if result.synthesis else ""

    if circuit_id:
        circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
        if circuit:
            circuit.blueprint_json = json.dumps(blueprint)
            circuit.netlist = netlist
            if result.title:
                circuit.name = result.title
            db.commit()
            db.refresh(circuit)
            return circuit.id

    circuit = Circuit(
        user_id=user_id,
        name=result.title or "Untitled Circuit",
        netlist=netlist,
        blueprint_json=json.dumps(blueprint),
    )
    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit.id


def run_pipeline_with_context(
    db: DBSession,
    *,
    prompt: str,
    circuit_id: Optional[int] = None,
    user_id: Optional[int] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    run_simulation: bool = True,
) -> PipelineRunResult:
    existing_blueprint = None
    if circuit_id:
        existing_blueprint = load_existing_blueprint(db, circuit_id)

    pipeline = NetlistGenerationPipeline(
        api_key=api_key,
        api_base=api_base,
        model=model,
    )

    result = pipeline.run(
        prompt=prompt,
        existing_blueprint=existing_blueprint,
        run_simulation=run_simulation,
    )

    returned_circuit_id = persist_circuit(
        db,
        circuit_id=circuit_id,
        user_id=user_id,
        prompt=prompt,
        result=result,
    )

    return PipelineRunResult(result=result, circuit_id=returned_circuit_id)
