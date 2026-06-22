from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CircuitCreateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    netlist: str = Field(..., min_length=1)


class CircuitUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    netlist: Optional[str] = Field(default=None, min_length=1)


class CircuitResponse(BaseModel):
    id: int
    user_id: Optional[int]
    name: Optional[str]
    netlist: str
    created_at: datetime
    updated_at: datetime


class CircuitListItem(BaseModel):
    id: int
    name: Optional[str]
    created_at: datetime
    updated_at: datetime

class CircuitHeadingUpdateRequest(BaseModel):
    name: str
