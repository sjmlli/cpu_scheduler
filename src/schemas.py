from pydantic import BaseModel
from typing import List, Optional

class Process(BaseModel):
    id: str
    burst_time: int
    priority: Optional[int] = None

class SchedulingRequest(BaseModel):
    processes: List[Process]

class SchedulingResponse(BaseModel):
    results: List[Process]
    average_waiting_time: float
    average_turnaround_time: float