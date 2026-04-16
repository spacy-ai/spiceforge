from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    op = "op"
    ac = "ac"
    dc = "dc"
    tran = "tran"
    tf = "tf"
    noise = "noise"
    pz = "pz"
    unknown = "unknown"


class SimulationOptions(BaseModel):
    timeout_seconds: int = Field(20, ge=1, le=120)
    max_output_kb: int = Field(512, ge=16, le=4096)
    preserve_artifacts: bool = False
    include_schematic: bool = False
    save_schematic_to_project_root: bool = False


class SimulationRequest(BaseModel):
    netlist: str = Field(..., min_length=1)
    options: Optional[SimulationOptions] = None


class MeasureBandwidthRequest(BaseModel):
    netlist: str = Field(..., min_length=1)
    start_freq: float = Field(1.0, gt=0)
    stop_freq: float = Field(1e6, gt=0)
    points_per_decade: int = Field(10, ge=1, le=1000)
    threshold_db: float = Field(-3.0, lt=0)
    timeout_seconds: int = Field(20, ge=1, le=120)


class MeasureGainRequest(BaseModel):
    netlist: str = Field(..., min_length=1)
    frequency_hz: float = Field(..., gt=0)
    start_freq: float = Field(1.0, gt=0)
    stop_freq: float = Field(1e6, gt=0)
    points_per_decade: int = Field(10, ge=1, le=1000)
    timeout_seconds: int = Field(20, ge=1, le=120)


class MeasureDcRequest(BaseModel):
    netlist: str = Field(..., min_length=1)
    node_name: str = Field(..., min_length=1)
    timeout_seconds: int = Field(20, ge=1, le=120)


class MeasureTransientRequest(BaseModel):
    netlist: str = Field(..., min_length=1)
    stop_time: float = Field(..., gt=0)
    step_time: float = Field(..., gt=0)
    startup_time: Optional[float] = Field(default=None, ge=0)
    timeout_seconds: int = Field(20, ge=1, le=120)


class MeasurePowerRequest(BaseModel):
    netlist: str = Field(..., min_length=1)
    timeout_seconds: int = Field(20, ge=1, le=120)


class AnalysisResult(BaseModel):
    analysis: AnalysisType
    data: Dict[str, Any] = Field(default_factory=dict)
    measurements: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class MeasurementResponse(BaseModel):
    status: str
    analysis: AnalysisType
    measurement: Dict[str, Any] = Field(default_factory=dict)
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    error: Optional["ErrorDetail"] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    hint: Optional[str] = None


class SchematicResult(BaseModel):
    format: str
    content: str
    saved_path: Optional[str] = None


class SimulationResponse(BaseModel):
    status: str
    analyses: List[AnalysisType]
    results: List[AnalysisResult] = Field(default_factory=list)
    schematic: Optional[SchematicResult] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    error: Optional[ErrorDetail] = None
