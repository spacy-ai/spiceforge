from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.circuit import Circuit
from app.models.user import User
from app.schema.export import ExportKicadRequest, ExportKicadResponse
from app.services.export_store import export_store
from app.services.kicad_export import create_kicad_export

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/kicad", response_model=ExportKicadResponse)
def export_kicad(
    payload: ExportKicadRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportKicadResponse:
    netlist = payload.netlist
    circuit_id = payload.circuit_id

    if circuit_id is not None:
        circuit = (
            db.query(Circuit)
            .filter(Circuit.id == circuit_id, Circuit.user_id == current_user.id)
            .first()
        )
        if circuit is None:
            raise HTTPException(status_code=404, detail="Circuit not found")
        netlist = circuit.netlist

    if not netlist or not netlist.strip():
        raise HTTPException(status_code=400, detail="Netlist is required")

    record, warnings = create_kicad_export(
        netlist=netlist,
        filename=payload.filename,
        user_id=current_user.id,
    )
    download_url = str(request.url_for("download_kicad", export_id=record.export_id))

    return ExportKicadResponse(
        status="success",
        export_id=record.export_id,
        filename=record.file_path.name,
        download_url=download_url,
        warnings=warnings,
        circuit_id=circuit_id,
    )


@router.get("/kicad/{export_id}")
def download_kicad(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    _ = db
    record = export_store.get(export_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    return FileResponse(
        record.file_path,
        media_type="application/octet-stream",
        filename=record.file_path.name,
    )
