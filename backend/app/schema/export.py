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
