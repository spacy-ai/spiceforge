from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ExportKicadRequest(BaseModel):
    circuit_id: Optional[int] = None
    netlist: Optional[str] = Field(default=None, min_length=1)
    filename: Optional[str] = None

    @model_validator(mode="after")
    def _require_source(self):
        if self.circuit_id is None and not self.netlist:
            raise ValueError("Provide circuit_id or netlist")
        return self


class ExportKicadResponse(BaseModel):
    status: str
    export_id: str
    filename: str
    download_url: str
    warnings: list[str] = Field(default_factory=list)
    circuit_id: Optional[int] = None
 
 
class ExportSvgRequest(BaseModel):
    netlist: str | None = Field(None, description="NGSpice netlist")
    circuit_id: int | None = Field(None, description="Circuit ID from database")
    format: str = Field("interactive", description="SVG format: 'interactive' or 'standard'")
    filename: str | None = Field(None, description="Custom filename for export")
    highlight_color: str = Field("#ffeb3b", description="Hover highlight color (hex)")
    highlight_opacity: float = Field(0.8, ge=0.0, le=1.0, description="Hover opacity")
    hover_stroke_width: int = Field(2, ge=1, le=10, description="Stroke width on hover")
 
 
class ExportSvgResponse(BaseModel):
    status: str
    export_id: str
    filename: str
    download_url: str
    format: str
    warnings: list[str]
    circuit_id: int | None
 