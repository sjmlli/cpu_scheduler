from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from scheduling.schemas import CompareRequest, SchedulingRequest, SchedulingResponse
from scheduling.service import compare_algorithms, execute_schedule


router = APIRouter()


@router.post("/execute", response_model=SchedulingResponse)
@router.post("/schedule", response_model=SchedulingResponse)
async def execute(req: SchedulingRequest):
    try:
        return execute_schedule(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/compare")
async def compare(req: CompareRequest):
    try:
        return compare_algorithms(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# Backwards-compatible endpoints
# ---------------------------------------------------------------------------


@router.post("/fcfs")
async def fcfs(payload: Any):
    return _legacy_execute("FCFS", payload)


@router.post("/sjf")
async def sjf(payload: Any):
    return _legacy_execute("SJF", payload)


@router.post("/spn")
async def spn(payload: Any):
    return _legacy_execute("SPN", payload)


@router.post("/srtf")
async def srtf(payload: Any):
    return _legacy_execute("SRTF", payload)


@router.post("/rr")
async def rr(payload: Any):
    return _legacy_execute("RR", payload)


@router.post("/hrrn")
async def hrrn(payload: Any):
    return _legacy_execute("HRRN", payload)


@router.post("/mlq")
async def mlq(payload: Any):
    return _legacy_execute("MLQ", payload)


@router.post("/mlfq")
async def mlfq(payload: Any):
    return _legacy_execute("MLFQ", payload)


def _legacy_execute(algorithm: str, payload: Any) -> Dict[str, Any]:
    req: Dict[str, Any] = {}
    if isinstance(payload, dict):
        req = dict(payload)
        req.setdefault("algorithm", algorithm)
    else:
        if not isinstance(payload, list):
            raise HTTPException(status_code=422, detail="Invalid request payload")
        processes: List[Dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                processes.append(item)
                continue
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                raise HTTPException(status_code=422, detail="Invalid process entry")
            pid = str(item[0])
            burst = int(item[1])
            pr = int(item[2]) if len(item) >= 3 else None
            processes.append({"pid": pid, "arrival_time": 0, "burst_time": burst, "priority": pr})
        req = {"algorithm": algorithm, "processes": processes}

    if algorithm in {"RR", "MLFQ"}:
        if "time_slice" not in req and "quantum" in req:
            req["time_slice"] = req["quantum"]

    try:
        parsed = SchedulingRequest.parse_obj(req)
        result = execute_schedule(parsed)
        return result.dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
