from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.circuit import Circuit
from app.schema.export import ExportSvgRequest, ExportSvgResponse
from app.services.svg_export import create_svg_export, ExportStore

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/svg", response_model=ExportSvgResponse)
def export_svg(
    payload: ExportSvgRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ExportSvgResponse:
    netlist = payload.netlist
    circuit_id = payload.circuit_id

    if circuit_id is not None:
        circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
        if circuit is None:
            raise HTTPException(status_code=404, detail="Circuit not found")
        netlist = circuit.netlist

    if not netlist or not netlist.strip():
        raise HTTPException(status_code=400, detail="Netlist is required")

    try:
        record, warnings = create_svg_export(
            db=db,
            netlist=netlist,
            format=payload.format,
            circuit_id=circuit_id,
            filename=payload.filename,
            highlight_color=payload.highlight_color,
            highlight_opacity=payload.highlight_opacity,
            hover_stroke_width=payload.hover_stroke_width,
            user_id=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SVG: {str(e)}")

    download_url = str(request.url_for("download_svg", export_id=record.export_id))

    return ExportSvgResponse(
        status="success",
        export_id=record.export_id,
        filename=f"{record.export_id}.svg",
        download_url=download_url,
        format=payload.format,
        warnings=warnings,
        circuit_id=circuit_id,
    )


@router.get("/svg/{export_id}")
def download_svg(
    export_id: str,
    db: Session = Depends(get_db),
):
    export_store = ExportStore(db)
    record = export_store.get_record(export_id)
    
    if record is None:
        raise HTTPException(status_code=404, detail="Export not found")
    
    media_type = "image/svg+xml"
    
    return Response(
        content=record.content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{record.export_id}.svg"'}
    )