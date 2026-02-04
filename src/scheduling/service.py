from __future__ import annotations

from typing import Any, Dict, List

from scheduling.engine import ProcState, simulate
from scheduling.policies import FCFS, HRRN, MLQ, MLFQ, RR, SJF, SRTF
from scheduling.schemas import (
    Averages,
    CompareRequest,
    GanttEntry,
    ProcessMetrics,
    SchedulingRequest,
    SchedulingResponse,
)


SUPPORTED_ALGOS = {"FCFS", "RR", "SJF", "SPN", "SRTF", "HRRN", "MLQ", "MLFQ"}


def _build_policy(req: SchedulingRequest, warnings: List[str]):
    algo = req.algorithm.upper()
    if algo not in SUPPORTED_ALGOS:
        raise ValueError(f"Unsupported algorithm: {algo}")

    if algo == "FCFS":
        return FCFS()
    if algo in {"SJF", "SPN"}:
        return SJF()
    if algo == "HRRN":
        return HRRN()
    if algo == "SRTF":
        return SRTF()
    if algo == "RR":
        if req.time_slice is None:
            raise ValueError("time_slice is required for RR")
        return RR(int(req.time_slice))
    if algo == "MLQ":
        cfg = req.config or {}
        queues = cfg.get("queues")
        if not isinstance(queues, list) or len(queues) != 4:
            ts = int(req.time_slice or 4)
            warnings.append("MLQ config.queues missing/invalid; using default: RR, RR, FCFS, FCFS")
            queues = [
                {"algorithm": "RR", "time_slice": ts},
                {"algorithm": "RR", "time_slice": ts},
                {"algorithm": "FCFS"},
                {"algorithm": "FCFS"},
            ]
        mapping = cfg.get("priority_mapping") or cfg.get("priorityMapping") or "1-4"
        return MLQ(queues=queues, priority_mapping=mapping)
    if algo == "MLFQ":
        cfg = req.config or {}
        slices = cfg.get("time_slices") or cfg.get("timeSlices")
        if slices is None:
            qs = cfg.get("queues")
            if isinstance(qs, list) and len(qs) == 4:
                slices = [q.get("time_slice") or q.get("timeSlice") for q in qs]
        if not isinstance(slices, list) or len(slices) != 4:
            if req.time_slice is None:
                raise ValueError("time_slice is required for MLFQ (or provide config.time_slices)")
            base = int(req.time_slice)
            warnings.append("MLFQ config time_slices missing/invalid; using default [ts, 2ts, 4ts, FCFS]")
            slices = [base, base * 2, base * 4, None]
        slices = [slices[0], slices[1], slices[2], None]
        return MLFQ(time_slices=slices)

    raise ValueError(f"Unsupported algorithm: {algo}")


def execute_schedule(req: SchedulingRequest) -> SchedulingResponse:
    warnings: List[str] = []
    policy = _build_policy(req, warnings)

    procs = [
        ProcState(
            pid=p.pid,
            arrival_time=int(p.arrival_time),
            burst_time=int(p.burst_time),
            priority=p.priority,
        )
        for p in req.processes
    ]

    gantt_segments, mutated = simulate(
        processes=procs,
        policy=policy,
        context_switch_time=int(req.context_switch_time),
    )

    by_pid = {p.pid: p for p in mutated}
    metrics: List[ProcessMetrics] = []
    wt_list: List[int] = []
    tat_list: List[int] = []
    rt_list: List[int] = []
    ct_list: List[int] = []

    for p_in in req.processes:
        p = by_pid[p_in.pid]
        if p.completion_time is None or p.first_start is None:
            raise ValueError(f"Process {p.pid} did not complete")
        ct = int(p.completion_time)
        tat = ct - int(p.arrival_time)
        wt = tat - int(p.burst_time)
        rt = int(p.first_start) - int(p.arrival_time)
        metrics.append(
            ProcessMetrics(
                pid=p.pid,
                waiting_time=wt,
                turnaround_time=tat,
                response_time=rt,
                completion_time=ct,
            )
        )
        wt_list.append(wt)
        tat_list.append(tat)
        rt_list.append(rt)
        ct_list.append(ct)

    n = len(metrics) or 1
    avg_wt = sum(wt_list) / n
    avg_tat = sum(tat_list) / n
    avg_rt = sum(rt_list) / n

    cpu_utilization = None
    throughput = None
    if gantt_segments:
        total_time = gantt_segments[-1].end - gantt_segments[0].start
        idle_time = sum(s.end - s.start for s in gantt_segments if s.pid == "IDLE")
        if total_time > 0:
            cpu_utilization = (total_time - idle_time) / total_time
            first_arr = min(p.arrival_time for p in procs)
            makespan = max(p.completion_time or 0 for p in procs) - first_arr
            throughput = (len(procs) / makespan) if makespan > 0 else None

    averages = Averages(
        avg_waiting_time=avg_wt,
        avg_turnaround_time=avg_tat,
        avg_response_time=avg_rt,
    )

    return SchedulingResponse(
        algorithm=req.algorithm.upper(),
        gantt=[GanttEntry(start=s.start, end=s.end, pid=s.pid) for s in gantt_segments],
        metrics=metrics,
        averages=averages,
        waiting_time=wt_list,
        turnaround_time=tat_list,
        response_time=rt_list,
        completion_time=ct_list,
        average_waiting_time=avg_wt,
        average_turnaround_time=avg_tat,
        average_response_time=avg_rt,
        avg_waiting_time=avg_wt,
        avg_turnaround_time=avg_tat,
        avg_response_time=avg_rt,
        cpu_utilization=cpu_utilization,
        throughput=throughput,
        warnings=warnings,
    )


def compare_algorithms(req: CompareRequest) -> Dict[str, Any]:
    algos = req.algorithms or ["FCFS", "RR", "SJF", "SPN", "SRTF", "HRRN", "MLQ", "MLFQ"]
    results: List[Dict[str, Any]] = []
    for a in algos:
        sreq = SchedulingRequest(
            algorithm=a,
            processes=req.processes,
            context_switch_time=req.context_switch_time,
            time_slice=req.time_slice,
            config=req.config,
        )
        res = execute_schedule(sreq)
        results.append(
            {
                "algorithm": res.algorithm,
                "avg_waiting_time": res.avg_waiting_time,
                "avg_turnaround_time": res.avg_turnaround_time,
                "avg_response_time": res.avg_response_time,
                "cpu_utilization": res.cpu_utilization,
                "throughput": res.throughput,
            }
        )
    return {"results": results}
