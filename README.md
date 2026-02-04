# CPU Scheduling Visualizer (Backend + Static Frontend)

## Run Backend

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

Backend runs on `http://localhost:8000`.

## Run Frontend (static)

```bash
cd frontend
python -m http.server 5173
```

Open `http://localhost:5173`.

## API

### Execute

`POST /execute` (alias: `POST /schedule`)

```json
{
  "algorithm": "SRTF",
  "processes": [
    {"pid": "P1", "arrival_time": 0, "burst_time": 8, "priority": 1},
    {"pid": "P2", "arrival_time": 1, "burst_time": 4, "priority": 2}
  ],
  "context_switch_time": 1,
  "time_slice": 4,
  "config": {}
}
```

Response includes:
- `gantt`: `{start,end,pid}` with `pid` in `{P*, IDLE, CS}`
- `metrics`: per-process `waiting_time/turnaround_time/response_time/completion_time`
- averages (`avg_*` + `average_*`) + optional `cpu_utilization` and `throughput`

### Compare

`POST /compare`

```json
{
  "algorithms": ["FCFS","RR","SRTF","HRRN","SJF","SPN","MLQ","MLFQ"],
  "processes": [
    {"pid":"P1","arrival_time":0,"burst_time":8,"priority":1},
    {"pid":"P2","arrival_time":1,"burst_time":4,"priority":2}
  ],
  "context_switch_time": 0,
  "time_slice": 4,
  "config": {}
}
```

## MLQ / MLFQ Config Notes

### MLQ (4Q)

`config.queues` must be a list of 4 objects:

```json
{
  "queues": [
    {"algorithm":"RR","time_slice":4},
    {"algorithm":"RR","time_slice":4},
    {"algorithm":"FCFS"},
    {"algorithm":"FCFS"}
  ],
  "priority_mapping": "1-4"
}
```

Priority mapping:
- `"1-4"` (default): priority 1..4 => queue 0..3 (1 highest)
- `"0-3"`: priority 0..3 => queue 0..3

### MLFQ (4Q)

Provide `config.time_slices` as length-4 list; last level is always FCFS.

```json
{ "time_slices": [4, 8, 16, null] }
```
