from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ProcState:
    pid: str
    arrival_time: int
    burst_time: int
    priority: Optional[int] = None

    remaining: int = field(init=False)
    first_start: Optional[int] = None
    completion_time: Optional[int] = None

    quantum_left: Optional[int] = None
    level: int = 0

    def __post_init__(self):
        self.remaining = int(self.burst_time)


@dataclass
class Segment:
    start: int
    end: int
    pid: str


def merge_segments(segments: List[Segment]) -> List[Segment]:
    if not segments:
        return []
    merged: List[Segment] = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        if seg.pid == last.pid and seg.start == last.end:
            last.end = seg.end
        else:
            merged.append(seg)
    return [s for s in merged if s.end > s.start]


class Policy:
    name: str
    preempt_on_arrival: bool = False

    def on_arrival(self, p: ProcState, now: int) -> None:  # pragma: no cover
        raise NotImplementedError

    def select(self, now: int, current: Optional[ProcState]) -> Optional[ProcState]:  # pragma: no cover
        raise NotImplementedError

    def max_continuous_run(self, p: ProcState, now: int) -> Optional[int]:
        return None

    def on_run(self, p: ProcState, ran_for: int, now: int) -> None:
        pass

    def on_timeslice_expired(self, p: ProcState, now: int) -> None:  # pragma: no cover
        raise NotImplementedError

    def put_back(self, p: ProcState, now: int) -> None:
        """Return a previously-selected process back to ready structures.

        Used when we inserted a context-switch (CS) segment and want to re-dispatch
        at the end of CS without losing the selected process.
        """
        # Default: treat it like a (re)arrival.
        self.on_arrival(p, now)


def simulate(
    processes: List[ProcState],
    policy: Policy,
    context_switch_time: int,
) -> Tuple[List[Segment], List[ProcState]]:
    """Run discrete-event simulation and return (gantt_segments, mutated_processes)."""

    n = len(processes)
    if n == 0:
        return [], processes

    # deterministic tie-break: arrival_time then pid
    arrival_sorted = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    idx = 0
    time = 0
    done = 0
    current: Optional[ProcState] = None
    segments: List[Segment] = []

    def next_arrival_time() -> Optional[int]:
        return arrival_sorted[idx].arrival_time if idx < n else None

    def push_arrivals(up_to: int) -> None:
        nonlocal idx
        while idx < n and arrival_sorted[idx].arrival_time <= up_to:
            p = arrival_sorted[idx]
            policy.on_arrival(p, p.arrival_time)
            idx += 1

    # If the first arrival is after t=0, show IDLE
    first_arrival = arrival_sorted[0].arrival_time
    if first_arrival > 0:
        segments.append(Segment(0, first_arrival, "IDLE"))
        time = first_arrival

    last_cpu_state: Optional[str] = segments[-1].pid if segments else None

    while done < n:
        push_arrivals(time)

        selected = policy.select(time, current)
        if selected is None:
            na = next_arrival_time()
            if na is None:
                break
            if na > time:
                segments.append(Segment(time, na, "IDLE"))
                last_cpu_state = "IDLE"
                time = na
            current = None
            continue

        # If the policy chose a different process than the current one, we're switching.
        if current is not None and selected.pid != current.pid:
            current = None

        # Context switch before starting a different pid (or after IDLE). No CS right at t=0.
        if (
            context_switch_time > 0
            and last_cpu_state is not None
            and last_cpu_state != "CS"
            and last_cpu_state != selected.pid
        ):
            # Put it back so it can be (re)selected after CS.
            policy.put_back(selected, time)
            segments.append(Segment(time, time + context_switch_time, "CS"))
            time += context_switch_time
            last_cpu_state = "CS"
            continue

        if selected.first_start is None:
            selected.first_start = time

        # max run length ignoring arrivals
        max_run = policy.max_continuous_run(selected, time)
        if max_run is None:
            max_run = selected.remaining
        max_run = min(max_run, selected.remaining)

        # For preemptive policies, cut at next arrival boundary so policy can decide to preempt.
        stop_at_arrival = None
        if policy.preempt_on_arrival:
            na = next_arrival_time()
            if na is not None and na > time:
                stop_at_arrival = na
                max_run = min(max_run, na - time)

        if max_run <= 0:
            na = next_arrival_time()
            if na is None:
                break
            if na > time:
                segments.append(Segment(time, na, "IDLE"))
                last_cpu_state = "IDLE"
                time = na
            current = None
            continue

        start = time
        end = time + max_run
        segments.append(Segment(start, end, selected.pid))
        last_cpu_state = selected.pid

        time = end
        selected.remaining -= max_run
        policy.on_run(selected, max_run, time)

        if selected.remaining == 0:
            selected.completion_time = time
            done += 1
            current = None
            continue

        if policy.preempt_on_arrival and stop_at_arrival is not None and time == stop_at_arrival:
            current = selected
            continue

        # timeslice forced yield
        policy.on_timeslice_expired(selected, time)
        current = None

    return merge_segments(segments), processes
