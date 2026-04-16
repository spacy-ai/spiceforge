from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.circuit import Circuit
from app.models.user import User
from app.schema.circuit import CircuitCreateRequest, CircuitResponse

router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.post("/", response_model=CircuitResponse)
def create_circuit(
    payload: CircuitCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CircuitResponse:
    circuit = Circuit(
        user_id=current_user.id,
        name=payload.name,
        netlist=payload.netlist,
    )
    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit


@router.get("/{circuit_id}", response_model=CircuitResponse)
def get_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CircuitResponse:
    circuit = (
        db.query(Circuit)
        .filter(Circuit.id == circuit_id, Circuit.user_id == current_user.id)
        .first()
    )
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit
