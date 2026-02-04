from __future__ import annotations

import heapq
from collections import deque
from typing import Deque, List, Optional, Tuple

from scheduling.engine import Policy, ProcState


def _key_arrival_pid(p: ProcState) -> Tuple[int, str]:
    return (p.arrival_time, p.pid)


class FCFS(Policy):
    name = "FCFS"
    preempt_on_arrival = False

    def __init__(self):
        self.q: Deque[ProcState] = deque()

    def on_arrival(self, p: ProcState, now: int) -> None:
        self.q.append(p)

    def put_back(self, p: ProcState, now: int) -> None:
        self.q.appendleft(p)

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is not None:
            return current
        return self.q.popleft() if self.q else None

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        return p.remaining

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        raise RuntimeError("FCFS has no time slice")


class SJF(Policy):
    """Non-preemptive shortest job first (a.k.a. SPN)."""

    name = "SJF"
    preempt_on_arrival = False

    def __init__(self):
        self.h: List[Tuple[int, int, str, ProcState]] = []

    def on_arrival(self, p: ProcState, now: int) -> None:
        heapq.heappush(self.h, (p.burst_time, p.arrival_time, p.pid, p))

    def put_back(self, p: ProcState, now: int) -> None:
        heapq.heappush(self.h, (p.burst_time, p.arrival_time, p.pid, p))

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is not None:
            return current
        return heapq.heappop(self.h)[-1] if self.h else None

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        return p.remaining

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        raise RuntimeError("SJF has no time slice")


class HRRN(Policy):
    """Highest Response Ratio Next (non-preemptive)."""

    name = "HRRN"
    preempt_on_arrival = False

    def __init__(self):
        self.ready: List[ProcState] = []

    def on_arrival(self, p: ProcState, now: int) -> None:
        self.ready.append(p)

    def put_back(self, p: ProcState, now: int) -> None:
        self.ready.insert(0, p)

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is not None:
            return current
        if not self.ready:
            return None

        best_i = 0
        best_rr = -1.0
        for i, p in enumerate(self.ready):
            waiting = max(0, now - p.arrival_time)
            rr = (waiting + p.burst_time) / p.burst_time
            if rr > best_rr:
                best_rr = rr
                best_i = i
            elif rr == best_rr:
                if _key_arrival_pid(p) < _key_arrival_pid(self.ready[best_i]):
                    best_i = i
        return self.ready.pop(best_i)

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        return p.remaining

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        raise RuntimeError("HRRN has no time slice")


class SRTF(Policy):
    """Shortest Remaining Time First (preemptive)."""

    name = "SRTF"
    preempt_on_arrival = True

    def __init__(self):
        self.h: List[Tuple[int, int, str, ProcState]] = []

    def on_arrival(self, p: ProcState, now: int) -> None:
        heapq.heappush(self.h, (p.remaining, p.arrival_time, p.pid, p))

    def put_back(self, p: ProcState, now: int) -> None:
        heapq.heappush(self.h, (p.remaining, p.arrival_time, p.pid, p))

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is None:
            return heapq.heappop(self.h)[-1] if self.h else None
        if not self.h:
            return current

        best = self.h[0][-1]
        best_key = (best.remaining, best.arrival_time, best.pid)
        cur_key = (current.remaining, current.arrival_time, current.pid)
        if best_key < cur_key:
            heapq.heappush(self.h, (current.remaining, current.arrival_time, current.pid, current))
            return heapq.heappop(self.h)[-1]
        return current

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        return p.remaining

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        raise RuntimeError("SRTF does not use fixed time slices")


class RR(Policy):
    name = "RR"
    preempt_on_arrival = False

    def __init__(self, quantum: int):
        if quantum <= 0:
            raise ValueError("time_slice must be > 0 for RR")
        self.quantum = int(quantum)
        self.q: Deque[ProcState] = deque()

    def on_arrival(self, p: ProcState, now: int) -> None:
        self.q.append(p)

    def put_back(self, p: ProcState, now: int) -> None:
        self.q.appendleft(p)

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is not None:
            if current.quantum_left is None or current.quantum_left <= 0:
                current.quantum_left = self.quantum
            return current
        if not self.q:
            return None
        p = self.q.popleft()
        if p.quantum_left is None or p.quantum_left <= 0:
            p.quantum_left = self.quantum
        return p

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        ql = self.quantum if (p.quantum_left is None or p.quantum_left <= 0) else int(p.quantum_left)
        return min(p.remaining, ql)

    def on_run(self, p: ProcState, ran_for: int, now: int) -> None:
        if p.quantum_left is None:
            p.quantum_left = self.quantum
        p.quantum_left -= ran_for

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        p.quantum_left = 0
        self.q.append(p)


class _QueueAlgo:
    """Internal queue logic used by MLQ."""

    def __init__(self, algo: str, quantum: Optional[int] = None):
        self.algo = (algo or "FCFS").strip().upper()
        self.quantum = int(quantum) if quantum is not None else None

        if self.algo == "RR":
            if not self.quantum or self.quantum <= 0:
                raise ValueError("RR queue requires time_slice > 0")
            self.q: Deque[ProcState] = deque()
        elif self.algo == "FCFS":
            self.q = deque()
        elif self.algo in {"SJF", "SPN"}:
            self.h: List[Tuple[int, int, str, ProcState]] = []
        elif self.algo == "HRRN":
            self.ready: List[ProcState] = []
        else:
            self.algo = "FCFS"
            self.q = deque()

    def add(self, p: ProcState) -> None:
        if self.algo in {"RR", "FCFS"}:
            self.q.append(p)
        elif self.algo in {"SJF", "SPN"}:
            heapq.heappush(self.h, (p.remaining, p.arrival_time, p.pid, p))
        else:
            self.ready.append(p)

    def empty(self) -> bool:
        if self.algo in {"RR", "FCFS"}:
            return not self.q
        if self.algo in {"SJF", "SPN"}:
            return not self.h
        return not self.ready

    def pick(self, now: int) -> Optional[ProcState]:
        if self.empty():
            return None
        if self.algo in {"RR", "FCFS"}:
            p = self.q.popleft()
            if self.algo == "RR" and (p.quantum_left is None or p.quantum_left <= 0):
                p.quantum_left = int(self.quantum)
            return p
        if self.algo in {"SJF", "SPN"}:
            return heapq.heappop(self.h)[-1]

        # HRRN
        best_i = 0
        best_rr = -1.0
        for i, p in enumerate(self.ready):
            waiting = max(0, now - p.arrival_time)
            rr = (waiting + p.remaining) / p.remaining
            if rr > best_rr:
                best_rr = rr
                best_i = i
            elif rr == best_rr:
                if _key_arrival_pid(p) < _key_arrival_pid(self.ready[best_i]):
                    best_i = i
        return self.ready.pop(best_i)

    def max_run(self, p: ProcState) -> int:
        if self.algo == "RR":
            ql = int(self.quantum) if (p.quantum_left is None or p.quantum_left <= 0) else int(p.quantum_left)
            return min(p.remaining, ql)
        return p.remaining

    def on_run(self, p: ProcState, ran_for: int) -> None:
        if self.algo == "RR":
            if p.quantum_left is None:
                p.quantum_left = int(self.quantum)
            p.quantum_left -= ran_for

    def on_timeslice_expired(self, p: ProcState) -> None:
        if self.algo == "RR":
            p.quantum_left = 0
            self.q.append(p)
        else:
            self.add(p)


class MLQ(Policy):
    name = "MLQ"
    preempt_on_arrival = True

    def __init__(self, queues: List[dict], priority_mapping: str = "1-4"):
        if len(queues) != 4:
            raise ValueError("MLQ requires exactly 4 queues")

        q_cfg = list(queues)
        if (q_cfg[3].get("algorithm") or "").strip().upper() == "RR":
            q_cfg[3] = {**q_cfg[3], "algorithm": "FCFS"}

        self.queues: List[_QueueAlgo] = []
        for cfg in q_cfg:
            algo = cfg.get("algorithm") or cfg.get("algo") or "FCFS"
            quantum = cfg.get("time_slice") or cfg.get("timeSlice")
            self.queues.append(_QueueAlgo(algo, quantum=quantum))

        self.priority_mapping = (priority_mapping or "1-4").strip()

    def _map_priority(self, priority: Optional[int]) -> int:
        if priority is None:
            return 3
        p = int(priority)
        if self.priority_mapping == "0-3":
            return max(0, min(3, p))
        return max(0, min(3, p - 1))

    def on_arrival(self, p: ProcState, now: int) -> None:
        q = self._map_priority(p.priority)
        p.level = q
        self.queues[q].add(p)

    def put_back(self, p: ProcState, now: int) -> None:
        q = int(getattr(p, "level", 3))
        q = max(0, min(3, q))
        qa = self.queues[q]
        if qa.algo in {"RR", "FCFS"}:
            qa.q.appendleft(p)
        elif qa.algo in {"SJF", "SPN"}:
            heapq.heappush(qa.h, (p.remaining, p.arrival_time, p.pid, p))
        else:
            qa.ready.insert(0, p)

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is not None:
            for q in range(0, current.level):
                if not self.queues[q].empty():
                    self.queues[current.level].add(current)
                    return self._pick_highest(now)
            return current
        return self._pick_highest(now)

    def _pick_highest(self, now: int) -> Optional[ProcState]:
        for q in range(4):
            if not self.queues[q].empty():
                p = self.queues[q].pick(now)
                if p is not None:
                    p.level = q
                return p
        return None

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        return self.queues[p.level].max_run(p)

    def on_run(self, p: ProcState, ran_for: int, now: int) -> None:
        self.queues[p.level].on_run(p, ran_for)

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        self.queues[p.level].on_timeslice_expired(p)


class MLFQ(Policy):
    name = "MLFQ"
    preempt_on_arrival = True

    def __init__(self, time_slices: List[Optional[int]]):
        if len(time_slices) != 4:
            raise ValueError("MLFQ requires exactly 4 levels")
        self.qs: List[Deque[ProcState]] = [deque() for _ in range(4)]

        self.time_slices: List[Optional[int]] = []
        for i, ts in enumerate(time_slices):
            if i < 3:
                if ts is None or int(ts) <= 0:
                    raise ValueError("MLFQ levels 0..2 require time_slice > 0")
                self.time_slices.append(int(ts))
            else:
                self.time_slices.append(None)

    def on_arrival(self, p: ProcState, now: int) -> None:
        p.level = 0
        p.quantum_left = 0
        self.qs[0].append(p)

    def put_back(self, p: ProcState, now: int) -> None:
        lvl = int(getattr(p, "level", 0))
        lvl = max(0, min(3, lvl))
        self.qs[lvl].appendleft(p)

    def put_back(self, p: ProcState, now: int) -> None:
        lvl = max(0, min(3, int(getattr(p, "level", 0))))
        self.qs[lvl].appendleft(p)

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:
        if current is not None:
            for lvl in range(0, current.level):
                if self.qs[lvl]:
                    self.qs[current.level].appendleft(current)
                    return self._pick_highest(now)
            return current
        return self._pick_highest(now)

    def _pick_highest(self, now: int) -> Optional[ProcState]:
        for lvl in range(4):
            if self.qs[lvl]:
                p = self.qs[lvl].popleft()
                p.level = lvl
                if lvl < 3:
                    if p.quantum_left is None or p.quantum_left <= 0:
                        p.quantum_left = int(self.time_slices[lvl])
                else:
                    p.quantum_left = None
                return p
        return None

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        if p.level == 3:
            return p.remaining
        ql = int(self.time_slices[p.level]) if (p.quantum_left is None or p.quantum_left <= 0) else int(p.quantum_left)
        return min(p.remaining, ql)

    def on_run(self, p: ProcState, ran_for: int, now: int) -> None:
        if p.level < 3:
            if p.quantum_left is None:
                p.quantum_left = int(self.time_slices[p.level])
            p.quantum_left -= ran_for

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:
        if p.level < 3:
            p.quantum_left = 0
            new_lvl = min(3, p.level + 1)
            p.level = new_lvl
            self.qs[new_lvl].append(p)
        else:
            self.qs[3].appendleft(p)
