"""Self-contained HTML/CSS/JS template for the CodePulse report.

Everything is inlined — no CDN, no external files. Opens offline in any
modern browser. Uses a custom squarified-treemap implementation instead
of D3.js to keep the bundle size manageable.
"""

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodePulse — __REPO_NAME_PLACEHOLDER__</title>
<style>
/* ── Reset & Base ───────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0a0b0f;
  --surface: rgba(255,255,255,0.03);
  --surface-hover: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.06);
  --border-hover: rgba(255,255,255,0.12);
  --text: #e2e8f0;
  --text-dim: #64748b;
  --text-muted: #475569;
  --cyan: #00e5ff;
  --cyan-glow: rgba(0,229,255,0.15);
  --green: #00e096;
  --green-glow: rgba(0,224,150,0.15);
  --amber: #ffaa00;
  --amber-glow: rgba(255,170,0,0.15);
  --red: #ff3d71;
  --red-glow: rgba(255,61,113,0.15);
  --critical: #9b1942;
  --critical-glow: rgba(155,25,66,0.2);
  --radius: 12px;
  --radius-sm: 8px;
  --font: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mono: 'SF Mono', 'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ── Layout ─────────────────────────────────────────────────────── */
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem 2rem 4rem;
}

/* ── Header ─────────────────────────────────────────────────────── */
.header {
  text-align: center;
  padding: 3rem 0 2rem;
  position: relative;
}

.header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}

.logo {
  font-size: 2.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--cyan), #7c3aed, var(--cyan));
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 4s ease-in-out infinite;
  letter-spacing: -1px;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.subtitle {
  color: var(--text-dim);
  margin-top: 0.5rem;
  font-size: 0.95rem;
}

.subtitle span { color: var(--text); font-weight: 500; }

/* ── Section Titles ─────────────────────────────────────────────── */
.section-title {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 2.5rem 0 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.section-title .icon { font-size: 1.4rem; }

/* ── Glass Card ─────────────────────────────────────────────────── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: border-color 0.2s, background 0.2s;
}

.card:hover {
  border-color: var(--border-hover);
  background: var(--surface-hover);
}

/* ── Animations ─────────────────────────────────────────────────── */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes countUp {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

.animate-in {
  opacity: 0;
  animation: fadeSlideUp 0.5s ease forwards;
}

/* ── No-Git Banner ──────────────────────────────────────────────── */
.no-git-banner {
  background: rgba(255,170,0,0.08);
  border: 1px solid rgba(255,170,0,0.2);
  border-radius: var(--radius-sm);
  padding: 0.8rem 1.2rem;
  color: var(--amber);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ── Hero Stats ─────────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0 2rem;
}

.stat-card {
  padding: 1.4rem 1.2rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 0 0 var(--radius) var(--radius);
}

.stat-card.cyan::after { background: var(--cyan); box-shadow: 0 0 12px var(--cyan-glow); }
.stat-card.amber::after { background: var(--amber); box-shadow: 0 0 12px var(--amber-glow); }
.stat-card.red::after { background: var(--red); box-shadow: 0 0 12px var(--red-glow); }
.stat-card.green::after { background: var(--green); box-shadow: 0 0 12px var(--green-glow); }

.stat-icon { font-size: 1.6rem; margin-bottom: 0.3rem; }

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  font-family: var(--mono);
  line-height: 1.2;
}

.stat-card.cyan .stat-value { color: var(--cyan); }
.stat-card.amber .stat-value { color: var(--amber); }
.stat-card.red .stat-value { color: var(--red); }
.stat-card.green .stat-value { color: var(--green); }

.stat-label {
  font-size: 0.8rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 0.2rem;
}

/* ── Treemap ────────────────────────────────────────────────────── */
.treemap-wrap {
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
  position: relative;
  background: var(--surface);
}

.treemap-container {
  width: 100%;
  height: 500px;
  position: relative;
  cursor: pointer;
}

.treemap-node {
  position: absolute;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px;
  transition: filter 0.15s, transform 0.15s;
  cursor: pointer;
  text-align: center;
}

.treemap-node:hover {
  filter: brightness(1.3);
  z-index: 10;
  border-color: rgba(255,255,255,0.3);
}

.treemap-node .node-name {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: rgba(255,255,255,0.9);
  text-shadow: 0 1px 3px rgba(0,0,0,0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  line-height: 1.3;
}

.treemap-node .node-risk {
  font-family: var(--mono);
  font-size: 0.65rem;
  color: rgba(255,255,255,0.7);
  text-shadow: 0 1px 3px rgba(0,0,0,0.8);
}

/* ── Tooltip ────────────────────────────────────────────────────── */
.tooltip {
  position: fixed;
  z-index: 1000;
  background: rgba(15,17,23,0.95);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--radius-sm);
  padding: 1rem 1.2rem;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  min-width: 260px;
  max-width: 340px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}

.tooltip.visible { opacity: 1; }

.tooltip-title {
  font-family: var(--mono);
  font-size: 0.85rem;
  color: var(--cyan);
  margin-bottom: 0.6rem;
  font-weight: 600;
  word-break: break-all;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.2rem 0;
  font-size: 0.8rem;
}

.tooltip-row .label { color: var(--text-dim); }
.tooltip-row .value { color: var(--text); font-weight: 600; font-family: var(--mono); }

.tooltip-divider {
  height: 1px;
  background: rgba(255,255,255,0.06);
  margin: 0.4rem 0;
}

/* ── Filters ────────────────────────────────────────────────────── */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  margin-bottom: 1rem;
  align-items: center;
}

.filter-bar input,
.filter-bar select {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 0.55rem 0.9rem;
  font-size: 0.85rem;
  font-family: var(--font);
  outline: none;
  transition: border-color 0.2s;
}

.filter-bar input:focus,
.filter-bar select:focus {
  border-color: var(--cyan);
}

.filter-bar input { flex: 1; min-width: 200px; }
.filter-bar select { min-width: 130px; cursor: pointer; }
.filter-bar select option { background: #1a1c24; }

/* ── Table ──────────────────────────────────────────────────────── */
.table-wrap {
  overflow-x: auto;
  border-radius: var(--radius);
  border: 1px solid var(--border);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

thead th {
  background: rgba(255,255,255,0.03);
  padding: 0.8rem 0.7rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.8px;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  position: sticky;
  top: 0;
  border-bottom: 1px solid var(--border);
  transition: color 0.2s;
}

thead th:hover { color: var(--cyan); }
thead th.sorted { color: var(--cyan); }

thead th .sort-arrow {
  display: inline-block;
  margin-left: 4px;
  font-size: 0.65rem;
  opacity: 0.4;
}

thead th.sorted .sort-arrow { opacity: 1; }

tbody tr {
  border-left: 4px solid transparent;
  transition: background 0.15s, border-color 0.15s;
  cursor: pointer;
}

tbody tr:hover { background: var(--surface-hover); }

tbody tr.risk-low { border-left-color: var(--green); }
tbody tr.risk-medium { border-left-color: var(--amber); }
tbody tr.risk-high { border-left-color: var(--red); }
tbody tr.risk-critical { border-left-color: var(--critical); }

tbody td {
  padding: 0.65rem 0.7rem;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  vertical-align: middle;
}

.file-path {
  font-family: var(--mono);
  font-size: 0.8rem;
  color: var(--text);
  max-width: 350px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Risk bar */
.risk-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.risk-bar-wrap {
  width: 60px;
  height: 6px;
  background: rgba(255,255,255,0.05);
  border-radius: 3px;
  overflow: hidden;
}

.risk-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.risk-num {
  font-family: var(--mono);
  font-weight: 700;
  font-size: 0.85rem;
  min-width: 28px;
}

/* Grade badge */
.grade-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-family: var(--mono);
  font-weight: 700;
  font-size: 0.75rem;
  text-align: center;
  min-width: 28px;
}

.grade-A { background: rgba(0,224,150,0.15); color: var(--green); }
.grade-B { background: rgba(0,229,255,0.15); color: var(--cyan); }
.grade-C { background: rgba(255,170,0,0.15); color: var(--amber); }
.grade-D { background: rgba(255,140,0,0.15); color: #ff8c00; }
.grade-E { background: rgba(255,61,113,0.15); color: var(--red); }
.grade-F { background: rgba(155,25,66,0.2); color: var(--red); }

/* MI colored text */
.mi-good { color: var(--green); }
.mi-moderate { color: var(--amber); }
.mi-poor { color: var(--red); }

/* ── Accordion (function details) ───────────────────────────────── */
.fn-row {
  display: none;
}

.fn-row.visible {
  display: table-row;
}

.fn-row td {
  padding: 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

.fn-detail {
  background: rgba(0,0,0,0.2);
  padding: 0.8rem 1rem 0.8rem 2.5rem;
}

.fn-list {
  list-style: none;
  font-family: var(--mono);
  font-size: 0.8rem;
}

.fn-list li {
  padding: 0.25rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.fn-list li::before {
  content: '├─';
  color: var(--text-muted);
}

.fn-list li:last-child::before {
  content: '└─';
}

.fn-name { color: var(--text); }
.fn-cc { color: var(--text-dim); margin-left: auto; }

/* ── Insights ───────────────────────────────────────────────────── */
.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.insight-card {
  padding: 1.2rem 1.4rem;
  border-left: 4px solid var(--cyan);
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.insight-card.type-danger { border-left-color: var(--red); }
.insight-card.type-critical { border-left-color: var(--critical); }
.insight-card.type-warning { border-left-color: var(--amber); }
.insight-card.type-info { border-left-color: var(--cyan); }

.insight-icon { font-size: 1.6rem; flex-shrink: 0; margin-top: 0.1rem; }

.insight-title {
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 0.3rem;
}

.insight-text {
  font-size: 0.85rem;
  color: var(--text-dim);
  line-height: 1.5;
}

.insight-files {
  margin-top: 0.4rem;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-muted);
}

.insight-files span {
  display: block;
  padding: 0.1rem 0;
}

/* ── Footer ─────────────────────────────────────────────────────── */
.footer {
  text-align: center;
  padding: 3rem 0 1rem;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.footer a {
  color: var(--cyan);
  text-decoration: none;
}

/* ── Responsive ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .container { padding: 1rem; }
  .logo { font-size: 2rem; }
  .treemap-container { height: 350px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .insights-grid { grid-template-columns: 1fr; }
  .file-path { max-width: 180px; }
}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <header class="header animate-in">
    <div class="logo">CodePulse</div>
    <div class="subtitle">
      <span>__REPO_NAME_PLACEHOLDER__</span> &mdash; Generated __GENERATED_AT_PLACEHOLDER__
    </div>
  </header>

  <!-- No-Git Banner (hidden by default) -->
  <div class="no-git-banner" id="noGitBanner" style="display:none">
    ⚠️ Git data unavailable — churn metrics excluded from analysis.
  </div>

  <!-- Hero Stats -->
  <div class="stats-grid" id="statsGrid"></div>

  <!-- Treemap -->
  <h2 class="section-title animate-in" style="animation-delay:0.2s">
    <span class="icon">🗺️</span> Complexity Treemap
  </h2>
  <div class="treemap-wrap animate-in" style="animation-delay:0.3s">
    <div class="treemap-container" id="treemap"></div>
  </div>

  <!-- Table -->
  <h2 class="section-title animate-in" style="animation-delay:0.4s">
    <span class="icon">📋</span> File Details
  </h2>
  <div class="filter-bar animate-in" style="animation-delay:0.45s">
    <input type="text" id="searchInput" placeholder="Search files...">
    <select id="riskFilter">
      <option value="all">Risk: All</option>
      <option value="low">🟢 Low</option>
      <option value="medium">🟡 Medium</option>
      <option value="high">🔴 High</option>
      <option value="critical">💀 Critical</option>
    </select>
    <select id="sortBy">
      <option value="risk">Sort: Risk ↓</option>
      <option value="cc">Sort: CC ↓</option>
      <option value="mi">Sort: MI ↑</option>
      <option value="churn">Sort: Churn ↓</option>
      <option value="loc">Sort: LOC ↓</option>
      <option value="name">Sort: Name ↑</option>
    </select>
    <select id="extFilter"></select>
  </div>
  <div class="table-wrap animate-in" style="animation-delay:0.5s">
    <table id="fileTable">
      <thead><tr id="tableHead"></tr></thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>

  <!-- Insights -->
  <h2 class="section-title animate-in" style="animation-delay:0.6s">
    <span class="icon">💡</span> Insights
  </h2>
  <div class="insights-grid" id="insightsGrid"></div>

  <!-- Footer -->
  <footer class="footer">
    Generated by <a href="https://github.com/ARYAN007H/codepulse" target="_blank">CodePulse</a>
    &bull; __GENERATED_AT_PLACEHOLDER__
  </footer>
</div>

<!-- Tooltip -->
<div class="tooltip" id="tooltip"></div>

<script>
/* ================================================================
   CodePulse Report — Client-side JavaScript
   ================================================================ */

// ── Data Injection ──
const DATA = __DATA_PLACEHOLDER__;
const INSIGHTS = __INSIGHTS_PLACEHOLDER__;
const REPO_NAME = "__REPO_NAME_PLACEHOLDER__";
const USE_GIT = __USE_GIT_PLACEHOLDER__;

// ── Utility Functions ──
function riskColor(score) {
  if (score <= 30) return '#00e096';
  if (score <= 50) return '#4ddb90';
  if (score <= 60) return '#ffaa00';
  if (score <= 75) return '#ff6b3d';
  if (score <= 85) return '#ff3d71';
  return '#9b1942';
}

function riskGradientColor(score) {
  // Smooth gradient: green → amber → red → dark red
  const stops = [
    { s: 0,   r: 0,   g: 224, b: 150 },
    { s: 40,  r: 77,  g: 219, b: 144 },
    { s: 55,  r: 255, g: 170, b: 0   },
    { s: 70,  r: 255, g: 107, b: 61  },
    { s: 82,  r: 255, g: 61,  b: 113 },
    { s: 100, r: 155, g: 25,  b: 66  },
  ];
  let lo = stops[0], hi = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (score >= stops[i].s && score <= stops[i + 1].s) {
      lo = stops[i]; hi = stops[i + 1]; break;
    }
  }
  const t = (hi.s === lo.s) ? 0 : (score - lo.s) / (hi.s - lo.s);
  const r = Math.round(lo.r + (hi.r - lo.r) * t);
  const g = Math.round(lo.g + (hi.g - lo.g) * t);
  const b = Math.round(lo.b + (hi.b - lo.b) * t);
  return `rgb(${r},${g},${b})`;
}

function basename(p) {
  const parts = p.replace(/\\/g, '/').split('/');
  return parts[parts.length - 1];
}

function tierEmoji(tier) {
  return { low: '🟢', medium: '🟡', high: '🔴', critical: '💀' }[tier] || '';
}

function gradeClass(g) { return 'grade-' + g; }

function miClass(g) { return 'mi-' + g; }

// ── Animated Counter ──
function animateCounter(el, target, duration = 800, isFloat = false) {
  const start = performance.now();
  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = target * eased;
    el.textContent = isFloat ? current.toFixed(1) : Math.round(current);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ── Stats Cards ──
function renderStats() {
  const grid = document.getElementById('statsGrid');
  const total = DATA.length;
  const hotspots = DATA.filter(d => d.risk_score > 60).length;
  const avgRisk = total ? DATA.reduce((a, d) => a + d.risk_score, 0) / total : 0;
  const avgCC = total ? DATA.reduce((a, d) => a + d.avg_cc, 0) / total : 0;
  const avgMI = total ? DATA.reduce((a, d) => a + d.mi_score, 0) / total : 0;

  const stats = [
    { icon: '📁', value: total, label: 'Files Analyzed', color: 'cyan', float: false },
    { icon: '⚠️', value: hotspots, label: 'Hotspots', color: hotspots > 0 ? 'red' : 'green', float: false },
    { icon: '📊', value: avgRisk, label: 'Avg Risk', color: 'amber', float: true },
    { icon: '🔥', value: avgCC, label: 'Avg Complexity', color: 'red', float: true },
    { icon: '🧪', value: avgMI, label: 'Avg Maintainability', color: 'green', float: true },
  ];

  stats.forEach((s, i) => {
    const card = document.createElement('div');
    card.className = `card stat-card ${s.color} animate-in`;
    card.style.animationDelay = `${0.1 + i * 0.08}s`;
    card.innerHTML = `
      <div class="stat-icon">${s.icon}</div>
      <div class="stat-value" id="stat-${i}">0</div>
      <div class="stat-label">${s.label}</div>
    `;
    grid.appendChild(card);
    // Animate after render
    setTimeout(() => {
      animateCounter(document.getElementById(`stat-${i}`), s.value, 900, s.float);
    }, 200 + i * 80);
  });
}

// ── Squarified Treemap Layout ──
function squarify(items, x, y, w, h) {
  const rects = [];
  if (!items.length || w <= 0 || h <= 0) return rects;

  const total = items.reduce((a, d) => a + d.value, 0);
  if (total <= 0) return rects;

  // Sort descending
  const sorted = items.slice().sort((a, b) => b.value - a.value);
  layoutRow(sorted, x, y, w, h, total, rects);
  return rects;
}

function layoutRow(items, x, y, w, h, total, rects) {
  if (!items.length) return;
  if (items.length === 1) {
    rects.push({ ...items[0], x, y, w, h });
    return;
  }

  const isWide = w >= h;
  let row = [];
  let rowArea = 0;
  const remaining = [...items];
  let bestRatio = Infinity;

  while (remaining.length) {
    const item = remaining[0];
    const testRow = [...row, item];
    const testArea = rowArea + item.value;
    const ratio = worstRatio(testRow, testArea, isWide ? h : w, total, isWide ? w : h);

    if (ratio <= bestRatio || row.length === 0) {
      row = testRow;
      rowArea = testArea;
      bestRatio = ratio;
      remaining.shift();
    } else {
      break;
    }
  }

  // Layout the row
  const rowFraction = rowArea / total;
  if (isWide) {
    const rowW = w * rowFraction;
    let cy = y;
    for (const item of row) {
      const itemH = h * (item.value / rowArea);
      rects.push({ ...item, x, y: cy, w: rowW, h: itemH });
      cy += itemH;
    }
    // Recurse on remaining
    if (remaining.length) {
      const newTotal = remaining.reduce((a, d) => a + d.value, 0);
      layoutRow(remaining, x + rowW, y, w - rowW, h, newTotal, rects);
    }
  } else {
    const rowH = h * rowFraction;
    let cx = x;
    for (const item of row) {
      const itemW = w * (item.value / rowArea);
      rects.push({ ...item, x: cx, y, w: itemW, h: rowH });
      cx += itemW;
    }
    if (remaining.length) {
      const newTotal = remaining.reduce((a, d) => a + d.value, 0);
      layoutRow(remaining, x, y + rowH, w, h - rowH, newTotal, rects);
    }
  }
}

function worstRatio(row, rowArea, sideLen, total, otherSide) {
  if (!row.length || rowArea <= 0 || total <= 0) return Infinity;
  const rowFraction = rowArea / total;
  const rowDim = otherSide * rowFraction;
  if (rowDim <= 0) return Infinity;

  let worst = 0;
  for (const item of row) {
    const itemFraction = item.value / rowArea;
    const itemDim = sideLen * itemFraction;
    if (itemDim <= 0) continue;
    const ratio = Math.max(rowDim / itemDim, itemDim / rowDim);
    if (ratio > worst) worst = ratio;
  }
  return worst;
}

// ── Render Treemap ──
function renderTreemap() {
  const container = document.getElementById('treemap');
  const rect = container.getBoundingClientRect();
  const W = rect.width;
  const H = rect.height;

  const items = DATA.filter(d => d.loc > 0).map(d => ({
    path: d.path,
    value: d.loc,
    risk: d.risk_score,
    data: d,
  }));

  if (!items.length) {
    container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-dim)">No data to visualize</div>';
    return;
  }

  const rects = squarify(items, 0, 0, W, H);
  const tooltip = document.getElementById('tooltip');

  rects.forEach((r, i) => {
    const node = document.createElement('div');
    node.className = 'treemap-node';
    node.style.left = r.x + 'px';
    node.style.top = r.y + 'px';
    node.style.width = r.w + 'px';
    node.style.height = r.h + 'px';
    node.style.background = riskGradientColor(r.risk);
    node.style.opacity = '0';
    node.style.animation = `fadeSlideUp 0.3s ease forwards`;
    node.style.animationDelay = `${0.3 + (i * 0.01)}s`;
    node.dataset.path = r.path;

    // Only show label if box is large enough
    if (r.w > 50 && r.h > 28) {
      const nameEl = document.createElement('div');
      nameEl.className = 'node-name';
      nameEl.textContent = basename(r.path);
      node.appendChild(nameEl);

      if (r.h > 44) {
        const riskEl = document.createElement('div');
        riskEl.className = 'node-risk';
        riskEl.textContent = Math.round(r.risk);
        node.appendChild(riskEl);
      }
    }

    // Tooltip on hover
    node.addEventListener('mouseenter', (e) => {
      const d = r.data;
      let html = `<div class="tooltip-title">${d.path}</div>`;
      html += `<div class="tooltip-row"><span class="label">Risk Score</span><span class="value" style="color:${riskColor(d.risk_score)}">${d.risk_score} / 100 ${tierEmoji(d.risk_tier)}</span></div>`;
      html += `<div class="tooltip-row"><span class="label">Complexity</span><span class="value"><span class="grade-badge ${gradeClass(d.cc_grade)}">${d.cc_grade}</span> avg ${d.avg_cc}</span></div>`;
      html += `<div class="tooltip-row"><span class="label">Maintainability</span><span class="value ${miClass(d.mi_grade)}">${d.mi_score}</span></div>`;
      html += `<div class="tooltip-divider"></div>`;
      if (USE_GIT) {
        html += `<div class="tooltip-row"><span class="label">Git Churn</span><span class="value">${d.commit_count} commits</span></div>`;
        html += `<div class="tooltip-row"><span class="label">Authors</span><span class="value">${d.unique_authors}</span></div>`;
        html += `<div class="tooltip-row"><span class="label">Last Changed</span><span class="value">${d.last_modified_human}</span></div>`;
        html += `<div class="tooltip-divider"></div>`;
      }
      html += `<div class="tooltip-row"><span class="label">Lines of Code</span><span class="value">${d.loc.toLocaleString()}</span></div>`;
      html += `<div class="tooltip-row"><span class="label">Functions</span><span class="value">${d.num_functions}</span></div>`;
      tooltip.innerHTML = html;
      tooltip.classList.add('visible');
    });

    node.addEventListener('mousemove', (e) => {
      const tx = Math.min(e.clientX + 16, window.innerWidth - tooltip.offsetWidth - 16);
      const ty = Math.min(e.clientY + 16, window.innerHeight - tooltip.offsetHeight - 16);
      tooltip.style.left = tx + 'px';
      tooltip.style.top = ty + 'px';
    });

    node.addEventListener('mouseleave', () => {
      tooltip.classList.remove('visible');
    });

    // Click to scroll to table row
    node.addEventListener('click', () => {
      const row = document.getElementById('row-' + CSS.escape(r.path));
      if (row) {
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        row.style.background = 'rgba(0,229,255,0.08)';
        setTimeout(() => { row.style.background = ''; }, 2000);
      }
    });

    container.appendChild(node);
  });
}

// ── Table Rendering ──
let currentSort = { key: 'risk', asc: false };
let expandedRows = new Set();

function getColumns() {
  const cols = [
    { key: 'path', label: 'File', sortable: true },
    { key: 'risk_score', label: 'Risk', sortable: true },
    { key: 'cc_grade', label: 'Grade', sortable: true },
    { key: 'avg_cc', label: 'CC Avg', sortable: true },
    { key: 'max_cc', label: 'CC Max', sortable: true },
    { key: 'mi_score', label: 'MI', sortable: true },
  ];
  if (USE_GIT) {
    cols.push({ key: 'commit_count', label: 'Churn', sortable: true });
    cols.push({ key: 'unique_authors', label: 'Authors', sortable: true });
    cols.push({ key: 'last_modified_human', label: 'Last Modified', sortable: true });
  }
  cols.push({ key: 'loc', label: 'LOC', sortable: true });
  return cols;
}

function renderTableHead() {
  const tr = document.getElementById('tableHead');
  tr.innerHTML = '';
  const cols = getColumns();
  cols.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col.label;
    th.dataset.key = col.key;
    const arrow = document.createElement('span');
    arrow.className = 'sort-arrow';
    arrow.textContent = '▼';
    th.appendChild(arrow);
    th.addEventListener('click', () => handleSort(col.key));
    tr.appendChild(th);
  });
}

function handleSort(key) {
  if (currentSort.key === key) {
    currentSort.asc = !currentSort.asc;
  } else {
    currentSort.key = key;
    currentSort.asc = key === 'path' || key === 'mi_score';
  }
  renderTable();
}

function getFilteredSorted() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  const riskFilter = document.getElementById('riskFilter').value;
  const extFilter = document.getElementById('extFilter').value;
  const sortKey = document.getElementById('sortBy').value;

  let filtered = DATA.filter(d => {
    if (search && !d.path.toLowerCase().includes(search)) return false;
    if (riskFilter !== 'all' && d.risk_tier !== riskFilter) return false;
    if (extFilter !== 'all' && d.extension !== extFilter) return false;
    return true;
  });

  // Sort
  const keyMap = {
    risk: 'risk_score', cc: 'avg_cc', mi: 'mi_score',
    churn: 'commit_count', loc: 'loc', name: 'path',
  };
  const sk = keyMap[sortKey] || currentSort.key;
  const asc = sortKey === 'name' || sortKey === 'mi' ? true : false;

  if (currentSort.key && document.getElementById('sortBy').value === sortKey) {
    // Use column header sort
  }

  filtered.sort((a, b) => {
    let va = a[sk], vb = b[sk];
    if (typeof va === 'string') {
      return asc ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    return asc ? va - vb : vb - va;
  });

  return filtered;
}

function renderTable() {
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';
  const filtered = getFilteredSorted();

  // Update column sort indicators
  document.querySelectorAll('#tableHead th').forEach(th => {
    th.classList.remove('sorted');
    th.querySelector('.sort-arrow').textContent = '▼';
  });

  filtered.forEach(d => {
    const tr = document.createElement('tr');
    tr.id = 'row-' + d.path;
    tr.className = 'risk-' + d.risk_tier;

    // File
    let html = `<td><div class="file-path" title="${d.path}">${d.path}</div></td>`;

    // Risk
    const color = riskColor(d.risk_score);
    html += `<td><div class="risk-cell">
      <span class="risk-num" style="color:${color}">${Math.round(d.risk_score)}</span>
      <div class="risk-bar-wrap"><div class="risk-bar" style="width:${d.risk_score}%;background:${color}"></div></div>
    </div></td>`;

    // Grade
    html += `<td><span class="grade-badge ${gradeClass(d.cc_grade)}">${d.cc_grade}</span></td>`;

    // CC Avg
    html += `<td style="font-family:var(--mono)">${d.avg_cc}</td>`;

    // CC Max
    html += `<td style="font-family:var(--mono)">${d.max_cc}</td>`;

    // MI
    html += `<td class="${miClass(d.mi_grade)}" style="font-family:var(--mono)">${d.mi_score}</td>`;

    // Git columns
    if (USE_GIT) {
      html += `<td style="font-family:var(--mono)">${d.commit_count}</td>`;
      html += `<td>${d.unique_authors}</td>`;
      html += `<td style="color:var(--text-dim)">${d.last_modified_human}</td>`;
    }

    // LOC
    html += `<td style="font-family:var(--mono)">${d.loc.toLocaleString()}</td>`;

    tr.innerHTML = html;

    // Click to expand functions
    tr.addEventListener('click', () => toggleFunctions(d, tr));
    tbody.appendChild(tr);

    // If expanded, show function row
    if (expandedRows.has(d.path)) {
      tbody.appendChild(createFnRow(d));
    }
  });
}

function toggleFunctions(d, tr) {
  if (expandedRows.has(d.path)) {
    expandedRows.delete(d.path);
  } else {
    expandedRows.add(d.path);
  }
  renderTable();
}

function createFnRow(d) {
  const fnTr = document.createElement('tr');
  fnTr.className = 'fn-row visible';
  const cols = getColumns().length;
  const td = document.createElement('td');
  td.colSpan = cols;

  if (!d.functions || d.functions.length === 0) {
    td.innerHTML = '<div class="fn-detail" style="color:var(--text-dim)">No functions found in this file.</div>';
  } else {
    let html = '<div class="fn-detail"><ul class="fn-list">';
    d.functions.forEach(fn => {
      html += `<li>
        <span class="fn-name">${fn.fullname || fn.name}()</span>
        <span class="fn-cc">CC: ${fn.complexity} <span class="grade-badge ${gradeClass(fn.grade)}">${fn.grade}</span></span>
      </li>`;
    });
    html += '</ul></div>';
    td.innerHTML = html;
  }

  fnTr.appendChild(td);
  return fnTr;
}

// ── Extension Filter ──
function populateExtFilter() {
  const sel = document.getElementById('extFilter');
  const exts = [...new Set(DATA.map(d => d.extension))].sort();
  sel.innerHTML = '<option value="all">Ext: All</option>';
  exts.forEach(e => {
    const opt = document.createElement('option');
    opt.value = e;
    opt.textContent = `.${e}`;
    sel.appendChild(opt);
  });
}

// ── Insights ──
function renderInsights() {
  const grid = document.getElementById('insightsGrid');
  if (!INSIGHTS.length) {
    grid.innerHTML = '<div class="card" style="padding:2rem;text-align:center;color:var(--text-dim)">No insights to display.</div>';
    return;
  }

  INSIGHTS.forEach((ins, i) => {
    const card = document.createElement('div');
    card.className = `card insight-card type-${ins.type} animate-in`;
    card.style.animationDelay = `${0.6 + i * 0.08}s`;

    let html = `<div class="insight-icon">${ins.icon}</div><div>`;
    html += `<div class="insight-title">${ins.title}</div>`;
    html += `<div class="insight-text">${ins.text}</div>`;
    if (ins.files && ins.files.length) {
      html += '<div class="insight-files">';
      ins.files.forEach(f => { html += `<span>→ ${f}</span>`; });
      html += '</div>';
    }
    html += '</div>';
    card.innerHTML = html;
    grid.appendChild(card);
  });
}

// ── No-Git Banner ──
function checkGitBanner() {
  if (!USE_GIT) {
    document.getElementById('noGitBanner').style.display = 'flex';
  }
}

// ── Event Listeners ──
document.getElementById('searchInput').addEventListener('input', renderTable);
document.getElementById('riskFilter').addEventListener('change', renderTable);
document.getElementById('sortBy').addEventListener('change', renderTable);
document.getElementById('extFilter').addEventListener('change', renderTable);

// Handle treemap resize
let resizeTimeout;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    document.getElementById('treemap').innerHTML = '';
    renderTreemap();
  }, 250);
});

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  checkGitBanner();
  renderStats();
  renderTreemap();
  populateExtFilter();
  renderTableHead();
  renderTable();
  renderInsights();
});
</script>
</body>
</html>'''
