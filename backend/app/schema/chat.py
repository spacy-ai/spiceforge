from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    model: Optional[str] = None
    run_simulation: bool = True


class ChatModifyRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    model: Optional[str] = None


class ChatExplainRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    model: Optional[str] = None


class SimulationInfo(BaseModel):
    success: bool
    analyses: list[str] = []
    results: list[dict] = []
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    convergence_failures: list[str] = []


class ChatResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    intent: Optional[str] = None
    summary: str = ""
    blueprint: Optional[dict] = None
    netlist: Optional[str] = None
    changes_summary: Optional[str] = None
    clarifications: list[str] = []
    error: Optional[str] = None
    simulation: Optional[SimulationInfo] = None


class SessionInfoResponse(BaseModel):
    session_id: str
    conversation_history: list[dict]
    blueprint: Optional[dict] = None
    netlist: str = ""
    created_at: str
    updated_at: str
