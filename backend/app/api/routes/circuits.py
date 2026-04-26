from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, get_optional_current_user
from app.models.circuit import Circuit
from app.models.user import User
from app.schema.circuit import CircuitCreateRequest, CircuitListItem, CircuitResponse, CircuitUpdateRequest
from app.core.schematic import render_schematic_png
from app.services.schematic import generate_schematic

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


@router.get("/{circuit_id}/svg")
def get_circuit_svg(
    circuit_id: int,
    renderer: str = Query("interactive", pattern="^(schemdraw|interactive)$"),
    width: int = Query(800, ge=200, le=4096),
    height: int = Query(600, ge=200, le=4096),
    db: Session = Depends(get_db),
) -> Response:
    circuit = _get_circuit_or_404(db, circuit_id)

    svg = generate_schematic(
        circuit.netlist,
        renderer=renderer,  # type: ignore[arg-type]
        width=width,
        height=height,
    )

    headers = {
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=svg.content, media_type="image/svg+xml", headers=headers)


@router.get("/{circuit_id}/png/download")
def download_circuit_svg(
    circuit_id: int,
    db: Session = Depends(get_db),
) -> Response:
    circuit = _get_circuit_or_404(db, circuit_id)
    png_data = render_schematic_png(circuit.netlist)
    headers = {
        "Content-Disposition": f'attachment; filename="circuit_{circuit_id}.png"',
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=png_data, media_type="image/png", headers=headers)
