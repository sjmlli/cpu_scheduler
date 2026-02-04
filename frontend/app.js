const $ = (id) => document.getElementById(id);

const ALGORITHMS = ["FCFS", "RR", "SRTF", "HRRN", "SJF", "SPN", "MLQ", "MLFQ"];

function hslFromString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
  const hue = hash % 360;
  return `hsl(${hue} 70% 40%)`;
}

function addRow({ pid = "P1", arrival = 0, burst = 1, priority = "" } = {}) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td class="py-2">
      <input class="w-28 px-2 py-1 rounded bg-slate-900 border border-slate-700 font-mono" value="${pid}" data-k="pid" />
    </td>
    <td class="py-2">
      <input type="number" min="0" class="w-24 px-2 py-1 rounded bg-slate-900 border border-slate-700" value="${arrival}" data-k="arrival" />
    </td>
    <td class="py-2">
      <input type="number" min="1" class="w-24 px-2 py-1 rounded bg-slate-900 border border-slate-700" value="${burst}" data-k="burst" />
    </td>
    <td class="py-2">
      <input type="number" min="0" class="w-28 px-2 py-1 rounded bg-slate-900 border border-slate-700" value="${priority}" data-k="priority" />
    </td>
    <td class="py-2 text-left">
      <button class="px-2 py-1 rounded bg-rose-700 hover:bg-rose-600 text-xs" data-act="del">Remove</button>
    </td>
  `;
  tr.querySelector('[data-act="del"]').addEventListener("click", () => tr.remove());
  $("procBody").appendChild(tr);
}

function readProcesses() {
  const rows = Array.from($("procBody").querySelectorAll("tr"));
  return rows
    .map((r) => {
      const pid = r.querySelector('[data-k="pid"]').value.trim();
      const arrival = Number(r.querySelector('[data-k="arrival"]').value);
      const burst = Number(r.querySelector('[data-k="burst"]').value);
      const prRaw = r.querySelector('[data-k="priority"]').value;
      const priority = prRaw === "" ? null : Number(prRaw);
      return { pid, arrival_time: arrival, burst_time: burst, priority };
    })
    .filter((p) => p.pid && Number.isFinite(p.arrival_time) && Number.isFinite(p.burst_time));
}

function parseConfig() {
  const raw = $("config").value.trim();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (e) {
    throw new Error("Config JSON نامعتبر است");
  }
}

function renderWarnings(warnings) {
  const el = $("warnings");
  el.innerHTML = "";
  if (!warnings || warnings.length === 0) return;
  el.innerHTML = warnings.map((w) => `⚠️ ${w}`).join("<br/>");
}

function renderGantt(gantt) {
  const bar = $("ganttBar");
  const axis = $("ganttAxis");
  bar.innerHTML = "";
  axis.innerHTML = "";
  if (!gantt || gantt.length === 0) return;

  for (const seg of gantt) {
    const dur = seg.end - seg.start;
    const cell = document.createElement("div");
    cell.className = "h-12 flex items-center justify-center border border-slate-950 text-xs font-semibold select-none";
    cell.style.flex = `${dur} 0 0`;
    if (seg.pid === "IDLE") {
      cell.style.background = "#334155";
      cell.textContent = "IDLE";
    } else if (seg.pid === "CS") {
      cell.style.background = "#b45309";
      cell.textContent = "CS";
    } else {
      cell.style.background = hslFromString(seg.pid);
      cell.textContent = seg.pid;
    }
    bar.appendChild(cell);
  }

  const bounds = [gantt[0].start, ...gantt.map((s) => s.end)];
  axis.innerHTML = `زمان: ${bounds.join("  |  ")}`;
}

function renderMetrics(metrics, averages, cpu_utilization, throughput) {
  const body = $("metricsBody");
  body.innerHTML = "";
  for (const m of metrics || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="py-2 font-mono">${m.pid}</td>
      <td class="py-2">${m.waiting_time}</td>
      <td class="py-2">${m.turnaround_time}</td>
      <td class="py-2">${m.response_time}</td>
      <td class="py-2">${m.completion_time}</td>
    `;
    body.appendChild(tr);
  }

  const avgEl = $("averages");
  const util = cpu_utilization == null ? "-" : (cpu_utilization * 100).toFixed(2) + "%";
  const thr = throughput == null ? "-" : throughput.toFixed(4);
  avgEl.innerHTML = `
    <div class="flex flex-wrap gap-4">
      <div><span class="text-slate-400">Avg WT:</span> ${averages?.avg_waiting_time?.toFixed?.(2) ?? "-"}</div>
      <div><span class="text-slate-400">Avg TAT:</span> ${averages?.avg_turnaround_time?.toFixed?.(2) ?? "-"}</div>
      <div><span class="text-slate-400">Avg RT:</span> ${averages?.avg_response_time?.toFixed?.(2) ?? "-"}</div>
      <div><span class="text-slate-400">CPU Util:</span> ${util}</div>
      <div><span class="text-slate-400">Throughput:</span> ${thr}</div>
    </div>
  `;
}

async function postJson(path, body) {
  const base = $("apiBase").value.replace(/\/$/, "");
  const res = await fetch(base + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail || "Request failed");
  return data;
}

async function execute() {
  const algorithm = $("algorithm").value;
  const processes = readProcesses();
  const context_switch_time = Number($("contextSwitch").value || 0);
  const time_slice = Number($("timeSlice").value || 0);
  const config = parseConfig();

  const req = { algorithm, processes, context_switch_time, config };
  if (time_slice > 0) req.time_slice = time_slice;

  const out = await postJson("/execute", req);
  renderWarnings(out.warnings);
  renderGantt(out.gantt);
  renderMetrics(out.metrics, out.averages, out.cpu_utilization, out.throughput);
}

function renderCompareList() {
  const wrap = $("compareList");
  wrap.innerHTML = "";
  for (const a of ALGORITHMS) {
    const id = `cmp_${a}`;
    const label = document.createElement("label");
    label.className = "flex items-center gap-2 px-2 py-1 rounded bg-slate-900 border border-slate-800";
    label.innerHTML = `<input type="checkbox" id="${id}" checked /> <span class="font-mono">${a}</span>`;
    wrap.appendChild(label);
  }
}

async function compare() {
  const processes = readProcesses();
  const context_switch_time = Number($("contextSwitch").value || 0);
  const time_slice = Number($("timeSlice").value || 0);
  const config = parseConfig();

  const algorithms = ALGORITHMS.filter((a) => $(`cmp_${a}`)?.checked);
  const req = { algorithms, processes, context_switch_time, config };
  if (time_slice > 0) req.time_slice = time_slice;

  const out = await postJson("/compare", req);
  const rows = (out.results || [])
    .map(
      (r) => `
        <tr class="border-t border-slate-800">
          <td class="py-2 font-mono">${r.algorithm}</td>
          <td class="py-2">${Number(r.avg_waiting_time).toFixed(2)}</td>
          <td class="py-2">${Number(r.avg_turnaround_time).toFixed(2)}</td>
          <td class="py-2">${Number(r.avg_response_time).toFixed(2)}</td>
        </tr>
      `
    )
    .join("");

  $("compareOut").innerHTML = `
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-slate-300">
          <tr>
            <th class="text-right py-2">Algorithm</th>
            <th class="text-right py-2">Avg WT</th>
            <th class="text-right py-2">Avg TAT</th>
            <th class="text-right py-2">Avg RT</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">${rows}</tbody>
      </table>
    </div>
  `;
}

function loadSample() {
  $("procBody").innerHTML = "";
  addRow({ pid: "P1", arrival: 0, burst: 8, priority: 1 });
  addRow({ pid: "P2", arrival: 1, burst: 4, priority: 2 });
  addRow({ pid: "P3", arrival: 2, burst: 9, priority: 3 });
  addRow({ pid: "P4", arrival: 3, burst: 5, priority: 4 });
}

// init
renderCompareList();
addRow({ pid: "P1", arrival: 0, burst: 5, priority: 1 });
addRow({ pid: "P2", arrival: 1, burst: 3, priority: 2 });
addRow({ pid: "P3", arrival: 2, burst: 8, priority: 3 });

$("addRow").addEventListener("click", () => addRow({ pid: `P${$("procBody").children.length + 1}` }));
$("loadSample").addEventListener("click", loadSample);
$("executeBtn").addEventListener("click", async () => {
  $("warnings").textContent = "";
  try {
    await execute();
  } catch (e) {
    $("warnings").textContent = String(e.message || e);
  }
});
$("compareBtn").addEventListener("click", async () => {
  $("compareOut").textContent = "";
  try {
    await compare();
  } catch (e) {
    $("compareOut").textContent = String(e.message || e);
  }
});
