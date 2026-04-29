const $ = (id) => document.getElementById(id);

function applyDeviceClass() {
  const ua = navigator.userAgent || "";
  const qs = new URLSearchParams(window.location.search);
  const forcedMobile = qs.get("mobile") === "1" || localStorage.getItem("okex_mobile_layout") === "1";
  const isMobileUA = /Android|iPhone|iPad|iPod|Mobile|Windows Phone/i.test(ua);
  const isTouchDevice = (navigator.maxTouchPoints || 0) > 1;
  const viewportWidth = Math.min(window.innerWidth || 9999, document.documentElement.clientWidth || 9999, window.screen?.width || 9999);
  const narrowScreen = viewportWidth <= 1200;
  if (forcedMobile || isMobileUA || isTouchDevice || narrowScreen) {
    document.documentElement.classList.add("mobile-layout");
    document.body.classList.add("mobile-layout");
  }
}

applyDeviceClass();
window.addEventListener("orientationchange", applyDeviceClass);
window.addEventListener("resize", applyDeviceClass);

let equityChart;
let btcChart;

async function fetchJSON(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

function num(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "--";
  const n = Number(value);
  if (!Number.isFinite(n)) return "--";
  return n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function pct(value) {
  if (value === null || value === undefined || value === "") return "--";
  const n = Number(value);
  if (!Number.isFinite(n)) return "--";
  return `${(n * 100).toFixed(2)}%`;
}

function signedClass(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n === 0) return "";
  return n > 0 ? "positive" : "negative";
}

function setText(id, value) {
  const el = $(id);
  if (el) el.textContent = value ?? "--";
}

function setSigned(id, value, formatter = num) {
  const el = $(id);
  if (!el) return;
  el.textContent = formatter(value);
  el.className = signedClass(value);
}

function actionClass(action) {
  const a = String(action || "").toLowerCase();
  if (a === "open") return "tag open";
  if (a === "add") return "tag add";
  if (a === "close") return "tag close";
  return "tag";
}

function renderRecordList(containerId, rows, mode = "trades") {
  const container = $(containerId);
  if (!rows.length) {
    container.innerHTML = `<div class="empty-record">No records yet</div>`;
    return;
  }
  container.innerHTML = rows.slice().reverse().map(row => `
    <article class="record-card ${String(row.action || "").toLowerCase()}">
      <div class="record-main">
        <span class="${actionClass(row.action)}">${row.action || "--"}</span>
        <strong>${row.side || "--"}</strong>
        <span class="record-time">${row.time || "--"}</span>
      </div>
      <div class="record-metrics">
        <div><span>Price</span><strong>${num(row.price)}</strong></div>
        <div><span>Size</span><strong>${num(row.size, 6)}</strong></div>
        <div><span>PnL</span><strong class="${signedClass(row.pnl)}">${num(row.pnl)}</strong></div>
        <div><span>Fee</span><strong>${num(row.fee)}</strong></div>
        <div><span>Balance</span><strong>${num(row.balance)}</strong></div>
        ${mode === "adds" ? `<div><span>Entry</span><strong>${num(row.entry)}</strong></div><div><span>Stop</span><strong>${num(row.stop)}</strong></div>` : `<div><span>Reason</span><strong>${row.reason || "--"}</strong></div>`}
      </div>
    </article>
  `).join("");
}

function renderPosition(status) {
  const p = status.position || {};
  const r = status.risk || {};
  const rows = [
    ["Side", p.side || "FLAT"],
    ["Entry", num(p.entry)],
    ["Size", num(p.size, 6)],
    ["Stop", num(p.stop)],
    ["Adds", p.adds ?? 0],
    ["Initial Entry", num(p.initial_entry)],
    ["Last Add Price", num(p.last_add_price)],
    ["Risk Amount", num(r.risk_amount)],
    ["Risk %", pct(r.risk_pct)],
    ["Locked Profit", num(r.locked_profit)],
    ["Locked Profit %", pct(r.locked_profit_pct)],
    ["Distance To Stop", num(r.distance_to_stop)],
    ["Distance To Stop %", pct(r.distance_to_stop_pct)],
  ];
  $("position-grid").innerHTML = rows.map(([k, v]) => `<div><span>${k}</span><strong>${v}</strong></div>`).join("");
}

function renderFileHealth(fileHealth) {
  const entries = Object.entries(fileHealth || {});
  $("file-health").innerHTML = entries.map(([name, info]) => `
    <tr>
      <td>${name}</td>
      <td><span class="health ${info.exists ? "ok" : "bad"}">${info.exists ? "exists" : "missing"}</span></td>
      <td>${info.size == null ? "--" : `${Number(info.size).toLocaleString()} B`}</td>
      <td>${info.modified || "--"}</td>
      <td class="path">${info.path || ""}</td>
    </tr>
  `).join("");
}

function renderParams(params) {
  $("strategy-params").innerHTML = Object.entries(params || {}).map(([k, v]) => `
    <div><span>${k}</span><strong>${v}</strong></div>
  `).join("");
}

function renderLogs(lines) {
  const html = (lines || []).map(line => {
    let cls = "";
    if (line.includes("ERROR")) cls = "error";
    else if (line.includes("ADD")) cls = "add";
    else if (line.includes("realtime_stop")) cls = "stop";
    else if (line.includes("BAR")) cls = "bar";
    return `<span class="${cls}">${line.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</span>`;
  }).join("\n");
  $("logs").innerHTML = html || "No logs";
}

function splitMarkers(trades) {
  const out = { OPEN: [], ADD: [], CLOSE: [] };
  for (const t of trades || []) {
    const action = String(t.action || "").toUpperCase();
    if (out[action] && t.time && t.price != null) out[action].push([t.time, Number(t.price), `${action} ${t.side || ""}`]);
  }
  return out;
}

function renderCharts(equityRows, trades) {
  if (!equityChart) equityChart = echarts.init($("equity-chart"));
  if (!btcChart) btcChart = echarts.init($("btc-chart"));

  const equityData = equityRows.filter(r => r.time).map(r => [r.time, r.equity]);
  const balanceData = equityRows.filter(r => r.time).map(r => [r.time, r.balance]);
  const closeData = equityRows.filter(r => r.time).map(r => [r.time, r.close]);
  equityChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { textStyle: { color: "#cbd5e1" } },
    grid: { left: 55, right: 20, top: 40, bottom: 45 },
    xAxis: { type: "time", axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "value", scale: true, axisLabel: { color: "#94a3b8" } },
    series: [
      { name: "Equity", type: "line", smooth: true, data: equityData, showSymbol: false },
      { name: "Balance", type: "line", smooth: true, data: balanceData, showSymbol: false },
    ]
  });

  const markers = splitMarkers(trades);
  btcChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { textStyle: { color: "#cbd5e1" } },
    grid: { left: 55, right: 20, top: 40, bottom: 45 },
    xAxis: { type: "time", axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "value", scale: true, axisLabel: { color: "#94a3b8" } },
    series: [
      { name: "BTC Close", type: "line", smooth: true, data: closeData, showSymbol: false },
      { name: "OPEN", type: "scatter", symbolSize: 12, data: markers.OPEN, itemStyle: { color: "#38bdf8" } },
      { name: "ADD", type: "scatter", symbol: "diamond", symbolSize: 13, data: markers.ADD, itemStyle: { color: "#f59e0b" } },
      { name: "CLOSE", type: "scatter", symbol: "triangle", symbolSize: 14, data: markers.CLOSE, itemStyle: { color: "#22c55e" } },
    ]
  });
}

async function refreshAll() {
  try {
    const [status, trades, adds, equityRows, logs] = await Promise.all([
      fetchJSON("/api/status"),
      fetchJSON("/api/trades?limit=50"),
      fetchJSON("/api/adds?limit=30"),
      fetchJSON("/api/equity?limit=500"),
      fetchJSON("/api/logs?limit=200"),
    ]);

    setText("title", status.title);
    setText("last-update", status.last_update);
    setText("last-candle", status.last_candle_ts);
    setText("balance", num(status.balance));
    setText("equity", num(status.equity));
    setSigned("unrealized", status.unrealized);
    setText("last-close", num(status.last_close));

    const s = status.trade_stats || {};
    setText("stat-total", s.total_rows);
    setText("stat-open", s.open_count);
    setText("stat-add", s.add_count);
    setText("stat-close", s.close_count);
    setSigned("stat-pnl", s.closed_pnl);
    setText("stat-fee", num(s.total_fee));
    setText("stat-add-fee", num(s.add_fee));

    setText("signal", status.signal);
    setText("atr", num(status.atr));
    setText("adx", num(status.adx));
    setText("adx-weight", num(status.adx_weight, 2));

    renderPosition(status);
    renderFileHealth(status.file_health);
    renderParams(status.strategy_params);
    renderRecordList("trades-list", trades, "trades");
    renderRecordList("adds-list", adds, "adds");
    renderLogs(logs);
    renderCharts(equityRows, trades);
  } catch (err) {
    console.error(err);
    setText("last-update", `Error: ${err.message}`);
  }
}

window.addEventListener("resize", () => {
  applyDeviceClass();
  equityChart && equityChart.resize();
  btcChart && btcChart.resize();
});

document.addEventListener("DOMContentLoaded", () => {
  const btn = $("mobile-toggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const enabled = !document.documentElement.classList.contains("mobile-layout");
    document.documentElement.classList.toggle("mobile-layout", enabled);
    document.body.classList.toggle("mobile-layout", enabled);
    localStorage.setItem("okex_mobile_layout", enabled ? "1" : "0");
    btn.textContent = enabled ? "Desktop View" : "Mobile View";
    setTimeout(() => {
      equityChart && equityChart.resize();
      btcChart && btcChart.resize();
    }, 50);
  });
  btn.textContent = document.documentElement.classList.contains("mobile-layout") ? "Desktop View" : "Mobile View";
});

refreshAll();
setInterval(refreshAll, 5000);