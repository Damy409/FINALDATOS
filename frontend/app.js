const colors = ["#2554d8", "#00a6b8", "#ef6f6c", "#f2a93b", "#7357d6", "#16a34a"];
let analysis = null;

document.getElementById("sampleBtn").addEventListener("click", loadSample);
document.getElementById("csvInput").addEventListener("change", uploadCsv);
document.getElementById("customerSelect").addEventListener("change", renderRecommendations);
document.getElementById("productSelect").addEventListener("change", renderRecommendations);

loadSample();

async function loadSample() {
  setStatus("Procesando datos de ejemplo con FastAPI...");
  const response = await fetch("/api/sample");
  await handleResponse(response);
}

async function uploadCsv(event) {
  const file = event.target.files[0];
  if (!file) return;
  setStatus(`Enviando ${file.name} al backend FastAPI...`);
  const form = new FormData();
  form.append("file", file);
  const response = await fetch("/api/upload", { method: "POST", body: form });
  await handleResponse(response);
}

async function handleResponse(response) {
  const payload = await response.json();
  if (!response.ok) {
    setStatus(payload.detail || "No se pudo procesar el archivo.", true);
    return;
  }
  analysis = payload;
  renderAll();
  setStatus("Analisis generado correctamente desde el backend Python/FastAPI.");
}

function renderAll() {
  text("sourceName", analysis.source.name);
  text("rows", format(analysis.source.rows));
  text("dates", `${analysis.source.date_min} a ${analysis.source.date_max}`);
  text("totalUnits", format(analysis.kpis.total_units));
  text("totalTransactions", format(analysis.kpis.total_transactions));
  text("totalCustomers", format(analysis.kpis.total_customers));
  text("totalProducts", format(analysis.kpis.total_products));

  barChart("topProducts", analysis.executive.top_products, "Unidades", colors[0]);
  barChart("topCustomers", analysis.executive.top_customers, "Transacciones", colors[1]);
  lineChart("dailyPeaks", analysis.executive.daily_peaks, "Transacciones", colors[2]);
  barChart("categories", analysis.executive.category_volume, "Unidades", colors[3]);
  lineChart("weekly", analysis.visuals.weekly_time_series, "Unidades", colors[4]);
  boxplot("boxplot", analysis.visuals.boxplot_by_category);
  heatmap("heatmap", analysis.visuals.correlation_heatmap);
  clusterPlot("clusters", analysis.advanced.customer_segments);
  fillRecommendationSelectors();
  renderRecommendations();
  renderInsights();
}

function barChart(id, data, unit, color) {
  const width = 720;
  const height = Math.max(300, data.length * 30 + 54);
  const max = Math.max(...data.map(item => item.value), 1);
  const rows = data.map((item, index) => {
    const y = 38 + index * 30;
    const barWidth = (item.value / max) * 420;
    return `<text x="12" y="${y + 15}" class="label">${escapeXml(item.label)}</text>
      <rect x="190" y="${y}" width="${barWidth}" height="18" rx="4" fill="${color}"></rect>
      <text x="${200 + barWidth}" y="${y + 14}" class="axis">${format(item.value)} ${unit}</text>`;
  }).join("");
  svg(id, width, height, rows);
}

function lineChart(id, data, unit, color) {
  const width = 720;
  const height = 320;
  const pad = 44;
  const max = Math.max(...data.map(item => item.value), 1);
  const step = data.length > 1 ? (width - pad * 2) / (data.length - 1) : 0;
  const points = data.map((item, index) => ({
    ...item,
    x: pad + index * step,
    y: height - pad - (item.value / max) * (height - pad * 2)
  }));
  const path = points.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" ");
  const dots = points.map(point => `<circle cx="${point.x}" cy="${point.y}" r="4" fill="${color}"><title>${point.label}: ${point.value}</title></circle>`).join("");
  const labels = points.filter((_, index) => index % Math.ceil(points.length / 6) === 0).map(point => `<text x="${point.x}" y="${height - 12}" text-anchor="middle" class="axis">${escapeXml(point.label)}</text>`).join("");
  svg(id, width, height, `
    <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#dbe3dc"></line>
    <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="#dbe3dc"></line>
    <path d="${path}" fill="none" stroke="${color}" stroke-width="3"></path>
    ${dots}${labels}
    <text x="${pad}" y="24" class="axis">Maximo: ${format(max)} ${unit}</text>`);
}

function boxplot(id, data) {
  const width = 720;
  const height = 330;
  const pad = 54;
  const max = Math.max(...data.map(item => item.max), 1);
  const slot = (width - pad * 2) / Math.max(data.length, 1);
  const body = data.map((item, index) => {
    const x = pad + index * slot + slot / 2;
    const y = value => height - pad - (value / max) * (height - pad * 2);
    return `<line x1="${x}" y1="${y(item.min)}" x2="${x}" y2="${y(item.max)}" stroke="${colors[index % colors.length]}" stroke-width="2"></line>
      <rect x="${x - 18}" y="${y(item.q3)}" width="36" height="${Math.max(2, y(item.q1) - y(item.q3))}" fill="${colors[index % colors.length]}" opacity="0.75"></rect>
      <line x1="${x - 22}" y1="${y(item.median)}" x2="${x + 22}" y2="${y(item.median)}" stroke="#162019" stroke-width="2"></line>
      <text x="${x}" y="${height - 14}" text-anchor="middle" class="axis">${escapeXml(short(item.label))}</text>`;
  }).join("");
  svg(id, width, height, body);
}

function heatmap(id, cells) {
  const rows = [...new Set(cells.map(cell => cell.row))];
  const cols = [...new Set(cells.map(cell => cell.column))];
  const tableRows = rows.map(row => `<tr><th>${escapeXml(row)}</th>${cols.map(col => {
    const value = cells.find(cell => cell.row === row && cell.column === col)?.value ?? 0;
    const shade = Math.round(245 - Math.abs(value) * 120);
    const bg = value >= 0 ? `rgb(${shade}, 242, ${shade})` : `rgb(245, ${shade}, ${shade})`;
    return `<td style="background:${bg}">${value.toFixed(2)}</td>`;
  }).join("")}</tr>`).join("");
  document.getElementById(id).innerHTML = `<table><thead><tr><th></th>${cols.map(col => `<th>${escapeXml(col)}</th>`).join("")}</tr></thead><tbody>${tableRows}</tbody></table>`;
}

function clusterPlot(id, data) {
  const width = 720;
  const height = 330;
  const pad = 48;
  const maxX = Math.max(...data.map(item => item.total_volume), 1);
  const maxY = Math.max(...data.map(item => item.distinct_products), 1);
  const body = data.map(item => {
    const x = pad + (item.total_volume / maxX) * (width - pad * 2);
    const y = height - pad - (item.distinct_products / maxY) * (height - pad * 2);
    return `<circle cx="${x}" cy="${y}" r="${5 + item.frequency}" fill="${colors[(item.cluster - 1) % colors.length]}" opacity="0.78">
      <title>${item.customer_id}: cluster ${item.cluster}</title>
    </circle>
    <text x="${x + 8}" y="${y - 8}" class="axis">${escapeXml(item.customer_id)}</text>`;
  }).join("");
  svg(id, width, height, `<line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#dbe3dc"></line>
    <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="#dbe3dc"></line>${body}
    <text x="${width / 2}" y="${height - 10}" text-anchor="middle" class="axis">Volumen total</text>`);
}

function fillRecommendationSelectors() {
  fillSelect("customerSelect", Object.keys(analysis.advanced.recommendations.customers).sort());
  fillSelect("productSelect", Object.keys(analysis.advanced.recommendations.products).sort());
}

function fillSelect(id, values) {
  const select = document.getElementById(id);
  const previous = select.value;
  select.innerHTML = values.map(value => `<option value="${escapeXml(value)}">${escapeXml(value)}</option>`).join("");
  if (values.includes(previous)) select.value = previous;
}

function renderRecommendations() {
  if (!analysis) return;
  const customer = document.getElementById("customerSelect").value;
  const product = document.getElementById("productSelect").value;
  renderRecList("customerRecs", analysis.advanced.recommendations.customers[customer] || []);
  renderRecList("productRecs", analysis.advanced.recommendations.products[product] || []);
}

function renderRecList(id, items) {
  document.getElementById(id).innerHTML = items.length
    ? `<ol>${items.map(item => `<li>${escapeXml(item.label)} <small>(${item.score})</small></li>`).join("")}</ol>`
    : "No hay recomendaciones suficientes.";
}

function renderInsights() {
  const clusterText = analysis.advanced.cluster_descriptions
    .map(item => `Cluster ${item.cluster}: ${item.customers} clientes, volumen promedio ${item.avg_volume}. ${item.interpretation}`)
    .join(" ");
  document.getElementById("insights").innerHTML = [
    ...analysis.insights,
    clusterText
  ].map(textValue => `<p>${escapeXml(textValue)}</p>`).join("");
}

function svg(id, width, height, body) {
  document.getElementById(id).innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img">${body}</svg>`;
}

function setStatus(message, error = false) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.style.color = error ? "#b83b3b" : "#66746a";
}

function text(id, value) {
  document.getElementById(id).textContent = value;
}

function format(value) {
  return Number(value).toLocaleString("es-CO");
}

function short(value) {
  return String(value).length > 10 ? `${String(value).slice(0, 9)}.` : value;
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
