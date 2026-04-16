from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.circuit import Circuit
from app.schema.circuit import CircuitCreateRequest, CircuitResponse
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
) -> CircuitResponse:
    circuit = Circuit(
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
) -> CircuitResponse:
    return _get_circuit_or_404(db, circuit_id)


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


@router.get("/{circuit_id}/svg/download")
def download_circuit_svg(
    circuit_id: int,
    db: Session = Depends(get_db),
) -> Response:
    circuit = _get_circuit_or_404(db, circuit_id)
    svg = generate_schematic(circuit.netlist, renderer="schemdraw")
    headers = {
        "Content-Disposition": f'attachment; filename="circuit_{circuit_id}.svg"',
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=svg.content, media_type="image/svg+xml", headers=headers)
