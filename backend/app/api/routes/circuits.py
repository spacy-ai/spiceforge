from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, get_optional_current_user
from app.models.circuit import Circuit
from app.models.user import User
from app.schema.circuit import CircuitCreateRequest, CircuitListItem, CircuitResponse, CircuitUpdateRequest, CircuitHeadingUpdateRequest

router = APIRouter(prefix="/circuits", tags=["circuits"])


def _get_circuit_or_404(db: Session, circuit_id: int) -> Circuit:
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit


@router.post("/", response_model=CircuitResponse)
def create_circuit(
    payload: CircuitCreateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> CircuitResponse:
    circuit = Circuit(
        user_id=current_user.id if current_user else None,
        name=payload.name,
        netlist=payload.netlist,
    )
    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit


@router.get("/me", response_model=list[CircuitListItem])
def list_my_circuits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CircuitListItem]:
    circuits = (
        db.query(Circuit)
        .filter(Circuit.user_id == current_user.id)
        .order_by(Circuit.updated_at.desc(), Circuit.created_at.desc())
        .all()
    )
    return circuits


@router.get("/{circuit_id}", response_model=CircuitResponse)
def get_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
) -> CircuitResponse:
    return _get_circuit_or_404(db, circuit_id)


@router.patch("/{circuit_id}", response_model=CircuitResponse)
def update_circuit(
    circuit_id: int,
    payload: CircuitUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CircuitResponse:
    circuit = _get_circuit_or_404(db, circuit_id)

    if circuit.user_id is None:
        circuit.user_id = current_user.id
    elif circuit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update circuit")

    if payload.name is not None:
        circuit.name = payload.name
    if payload.netlist is not None:
        circuit.netlist = payload.netlist

    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit


@router.patch("/{circuit_id}/heading", response_model=CircuitResponse)
def update_circuit_heading_public(
    circuit_id: int,
    payload: CircuitHeadingUpdateRequest,
    db: Session = Depends(get_db),
) -> CircuitResponse:
    circuit = _get_circuit_or_404(db, circuit_id)
    
    # Update only the name
    circuit.name = payload.name

    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit

