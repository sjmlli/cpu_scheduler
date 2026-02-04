import sys


sys.path.insert(0, "src")

from scheduling.schemas import SchedulingRequest
from scheduling.service import execute_schedule


def _sample_processes():
    return [
        {"pid": "P1", "arrival_time": 0, "burst_time": 8, "priority": 1},
        {"pid": "P2", "arrival_time": 1, "burst_time": 4, "priority": 2},
        {"pid": "P3", "arrival_time": 2, "burst_time": 9, "priority": 3},
        {"pid": "P4", "arrival_time": 3, "burst_time": 5, "priority": 4},
    ]


def test_all_algorithms_run():
    algos = ["FCFS", "RR", "SRTF", "HRRN", "SJF", "SPN", "MLQ", "MLFQ"]
    for algo in algos:
        req = SchedulingRequest.parse_obj(
            {
                "algorithm": algo,
                "processes": _sample_processes(),
                "context_switch_time": 1,
                "time_slice": 4,
                "config": {
                    "queues": [
                        {"algorithm": "RR", "time_slice": 4},
                        {"algorithm": "RR", "time_slice": 4},
                        {"algorithm": "FCFS"},
                        {"algorithm": "FCFS"},
                    ],
                    "time_slices": [4, 8, 16, None],
                },
            }
        )
        res = execute_schedule(req)
        assert res.algorithm == algo
        assert len(res.gantt) > 0
        assert len(res.metrics) == 4
        # Each metric field should be present and integer-ish.
        for m in res.metrics:
            assert isinstance(m.waiting_time, int)
            assert isinstance(m.turnaround_time, int)
            assert isinstance(m.response_time, int)
            assert isinstance(m.completion_time, int)


def test_idle_and_cs_are_emitted():
    req = SchedulingRequest.parse_obj(
        {
            "algorithm": "FCFS",
            "context_switch_time": 2,
            "processes": [
                {"pid": "P1", "arrival_time": 3, "burst_time": 4},
                {"pid": "P2", "arrival_time": 10, "burst_time": 2},
            ],
        }
    )
    res = execute_schedule(req)
    pids = [g.pid for g in res.gantt]
    assert "IDLE" in pids
    assert "CS" in pids
