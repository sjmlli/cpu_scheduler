from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class ProcessIn(BaseModel):
    pid: str
    arrival_time: int = 0
    burst_time: int
    priority: Optional[int] = None

    @root_validator(pre=True)
    def _normalize_keys(cls, values: Dict[str, Any]):
        v = dict(values or {})
        if "pid" not in v and "id" in v:
            v["pid"] = v.pop("id")
        if "arrival_time" not in v and "arrivalTime" in v:
            v["arrival_time"] = v.pop("arrivalTime")
        if "burst_time" not in v and "burstTime" in v:
            v["burst_time"] = v.pop("burstTime")
        if "priority" not in v and "prio" in v:
            v["priority"] = v.pop("prio")
        return v

    @validator("arrival_time")
    def _arrival_non_negative(cls, v: int):
        if v < 0:
            raise ValueError("arrival_time must be >= 0")
        return v

    @validator("burst_time")
    def _burst_positive(cls, v: int):
        if v <= 0:
            raise ValueError("burst_time must be > 0")
        return v


class SchedulingRequest(BaseModel):
    algorithm: str
    processes: List[ProcessIn]
    context_switch_time: int = 0
    time_slice: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)

    @root_validator(pre=True)
    def _normalize_request_keys(cls, values: Dict[str, Any]):
        v = dict(values or {})
        if "context_switch_time" not in v and "contextSwitchTime" in v:
            v["context_switch_time"] = v.pop("contextSwitchTime")
        if "time_slice" not in v and "timeSlice" in v:
            v["time_slice"] = v.pop("timeSlice")
        return v

    @validator("context_switch_time")
    def _cs_non_negative(cls, v: int):
        if v < 0:
            raise ValueError("context_switch_time must be >= 0")
        return v

    @validator("algorithm")
    def _algo_normalize(cls, v: str):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("algorithm is required")
        return v.strip().upper()


class CompareRequest(BaseModel):
    algorithms: Optional[List[str]] = None
    processes: List[ProcessIn]
    context_switch_time: int = 0
    time_slice: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)

    @root_validator(pre=True)
    def _normalize_keys(cls, values: Dict[str, Any]):
        v = dict(values or {})
        if "context_switch_time" not in v and "contextSwitchTime" in v:
            v["context_switch_time"] = v.pop("contextSwitchTime")
        if "time_slice" not in v and "timeSlice" in v:
            v["time_slice"] = v.pop("timeSlice")
        return v

    @validator("context_switch_time")
    def _cs_non_negative(cls, v: int):
        if v < 0:
            raise ValueError("context_switch_time must be >= 0")
        return v


class GanttEntry(BaseModel):
    start: int
    end: int
    pid: str


class ProcessMetrics(BaseModel):
    pid: str
    waiting_time: int
    turnaround_time: int
    response_time: int
    completion_time: int


class Averages(BaseModel):
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float


class SchedulingResponse(BaseModel):
    algorithm: str
    gantt: List[GanttEntry]
    metrics: List[ProcessMetrics]
    averages: Averages

    waiting_time: List[int]
    turnaround_time: List[int]
    response_time: List[int]
    completion_time: List[int]

    average_waiting_time: float
    average_turnaround_time: float
    average_response_time: float
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float

    cpu_utilization: Optional[float] = None
    throughput: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
