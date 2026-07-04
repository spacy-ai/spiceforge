from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SimulationInfo(BaseModel):
    success: bool
    analyses: list[str] = []
    results: list[dict] = []
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    convergence_failures: list[str] = []
