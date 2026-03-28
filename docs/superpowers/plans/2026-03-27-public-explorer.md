# OpenRouter Model Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static website where anyone can explore, filter, sort, and compare OpenRouter models and endpoints — powered by DuckDB-WASM running in the browser.

**Architecture:** Single-page vanilla JS app. DuckDB-WASM loads the `.duckdb` file as a static asset, runs a pre-joined SQL view, and feeds the results to a Tabulator table with row grouping by model. A facet sidebar builds `WHERE` clauses and re-queries DuckDB on each filter change. An optional SQL tab lets power users write arbitrary queries.

**Tech Stack:** DuckDB-WASM 1.30.0, Tabulator 6.3.1, vanilla JS (ES modules), CSS Grid for layout. No build step — CDN imports only.

---

## File Map

| File | Responsibility |
|---|---|
| `site/index.html` | App shell: CDN imports, layout containers, loading state |
| `site/style.css` | Layout grid, sidebar, table, SQL tab styling |
| `site/db.js` | DuckDB-WASM init, load `.duckdb` file, `query()` helper returning JS objects |
| `site/facets.js` | Render facet sidebar, read filter state, build SQL WHERE clause |
| `site/table.js` | Tabulator config: columns, grouping, formatters, data loading |
| `site/sql-tab.js` | SQL textarea, run button, results table |
| `site/app.js` | Main: init DB, create view, populate facets, wire events, render table |
| `site/public/openrouter.duckdb` | Static database file (copied from `data/`) |

---

## Task 1: HTML Shell & CSS Layout

**Files:**
- Create: `site/index.html`
- Create: `site/style.css`

- [ ] **Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenRouter Model Explorer</title>
    <link href="https://unpkg.com/tabulator-tables@6.3.1/dist/css/tabulator_midnight.min.css" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>OpenRouter Model Explorer</h1>
        <nav>
            <button id="tab-explore" class="tab active">Explore</button>
            <button id="tab-sql" class="tab">SQL</button>
        </nav>
    </header>
    <main id="view-explore">
        <aside id="facets">
            <div id="facets-loading">Loading filters...</div>
        </aside>
        <section id="table-container">
            <div id="loading">Loading database...</div>
            <div id="table"></div>
            <div id="status-bar"></div>
        </section>
    </main>
    <main id="view-sql" class="hidden">
        <div id="sql-editor">
            <textarea id="sql-input" spellcheck="false">SELECT m.name, e.provider_slug, e.latency_p50, e.throughput_p50
FROM model_endpoints e
JOIN models m ON m.slug = e.model_slug
WHERE e.latency_p50 IS NOT NULL
ORDER BY e.latency_p50 ASC
LIMIT 20</textarea>
            <button id="sql-run">Run (Ctrl+Enter)</button>
        </div>
        <div id="sql-error" class="hidden"></div>
        <div id="sql-results"></div>
    </main>
    <script src="https://unpkg.com/tabulator-tables@6.3.1/dist/js/tabulator.min.js"></script>
    <script type="module" src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create style.css**

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg: #0d1117;
    --bg-surface: #161b22;
    --bg-hover: #1c2128;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-surface);
}

header h1 { font-size: 16px; font-weight: 600; }

nav { display: flex; gap: 4px; }

.tab {
    padding: 6px 14px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 13px;
}

.tab.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
}

main#view-explore {
    display: grid;
    grid-template-columns: 240px 1fr;
    flex: 1;
    overflow: hidden;
}

aside#facets {
    padding: 16px;
    border-right: 1px solid var(--border);
    overflow-y: auto;
    background: var(--bg-surface);
    font-size: 13px;
}

#table-container {
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

#table { flex: 1; overflow: hidden; }

#loading {
    padding: 40px;
    text-align: center;
    color: var(--text-muted);
}

#status-bar {
    padding: 6px 16px;
    font-size: 12px;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
    background: var(--bg-surface);
}

.hidden { display: none !important; }

/* Facet sidebar */
.facet-group { margin-bottom: 16px; }
.facet-group label.facet-title {
    display: block;
    font-weight: 600;
    margin-bottom: 6px;
    color: var(--text);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.facet-group .facet-options { display: flex; flex-direction: column; gap: 2px; }
.facet-group .facet-options label {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 0;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-muted);
}
.facet-group .facet-options label:hover { color: var(--text); }
.facet-group input[type="range"] { width: 100%; accent-color: var(--accent); }
.facet-group .range-values {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--text-muted);
}

/* SQL tab */
main#view-sql {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

#sql-editor {
    padding: 16px;
    display: flex;
    gap: 8px;
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border);
}

#sql-input {
    flex: 1;
    min-height: 100px;
    padding: 10px;
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 13px;
    resize: vertical;
}

#sql-run {
    padding: 8px 16px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    align-self: flex-end;
}

#sql-error {
    padding: 12px 16px;
    background: #3d1f1f;
    color: #f97583;
    font-family: monospace;
    font-size: 13px;
}

#sql-results { flex: 1; overflow: hidden; }
```

- [ ] **Step 3: Verify layout loads**

Open `site/index.html` in a browser (or `python3 -m http.server 8000 -d site/`). Should see header, empty sidebar, "Loading database..." text.

- [ ] **Step 4: Commit**

```bash
git -c commit.gpgsign=false add site/index.html site/style.css
git -c commit.gpgsign=false commit -m "feat: HTML shell and CSS layout for model explorer"
```

---

## Task 2: DuckDB-WASM Initialization

**Files:**
- Create: `site/db.js`

- [ ] **Step 1: Create db.js**

```javascript
import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.30.0/+esm';

let db = null;
let conn = null;

export async function initDB(dbUrl) {
    const BUNDLES = duckdb.getJsDelivrBundles();
    const bundle = await duckdb.selectBundle(BUNDLES);

    const workerUrl = URL.createObjectURL(
        new Blob([`importScripts("${bundle.mainWorker}");`], { type: 'text/javascript' })
    );

    const worker = new Worker(workerUrl);
    const logger = new duckdb.ConsoleLogger();
    db = new duckdb.AsyncDuckDB(logger, worker);
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    URL.revokeObjectURL(workerUrl);

    // Fetch and register the .duckdb file
    const response = await fetch(dbUrl);
    const buffer = new Uint8Array(await response.arrayBuffer());
    await db.registerFileBuffer('openrouter.duckdb', buffer);
    await db.open({ path: 'openrouter.duckdb' });

    conn = await db.connect();
    return conn;
}

export async function query(sql) {
    if (!conn) throw new Error('Database not initialized');
    const result = await conn.query(sql);
    return result.toArray().map(row => row.toJSON());
}
```

- [ ] **Step 2: Copy the database file**

```bash
mkdir -p site/public
cp data/openrouter.duckdb site/public/openrouter.duckdb
```

- [ ] **Step 3: Commit**

```bash
git -c commit.gpgsign=false add site/db.js
git -c commit.gpgsign=false commit -m "feat: DuckDB-WASM init and query helper"
```

---

## Task 3: Tabulator Table Configuration

**Files:**
- Create: `site/table.js`

- [ ] **Step 1: Create table.js**

```javascript
let table = null;

const COLUMNS = [
    {
        title: "Provider", field: "provider", sorter: "string",
        headerFilter: "input", headerFilterPlaceholder: "Filter...",
        width: 130,
    },
    {
        title: "TTFT (ms)", field: "ttft_ms", sorter: "number",
        hozAlign: "right", width: 100,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "Tok/s", field: "tokens_per_sec", sorter: "number",
        hozAlign: "right", width: 80,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "$/M in", field: "input_price_per_m", sorter: "number",
        hozAlign: "right", width: 80,
        formatter: (cell) => {
            const v = cell.getValue();
            if (v == null) return '—';
            return v < 0.01 ? 'Free' : '$' + v.toFixed(2);
        },
    },
    {
        title: "$/M out", field: "output_price_per_m", sorter: "number",
        hozAlign: "right", width: 80,
        formatter: (cell) => {
            const v = cell.getValue();
            if (v == null) return '—';
            return v < 0.01 ? 'Free' : '$' + v.toFixed(2);
        },
    },
    {
        title: "Intel", field: "intelligence_index", sorter: "number",
        hozAlign: "right", width: 70,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) : '—';
        },
    },
    {
        title: "Code", field: "coding_index", sorter: "number",
        hozAlign: "right", width: 70,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) : '—';
        },
    },
    {
        title: "Agent", field: "agentic_index", sorter: "number",
        hozAlign: "right", width: 70,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) : '—';
        },
    },
    {
        title: "Context", field: "context_length", sorter: "number",
        hozAlign: "right", width: 90, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? (v / 1000).toFixed(0) + 'k' : '—';
        },
    },
    {
        title: "Reasoning", field: "supports_reasoning", sorter: "boolean",
        hozAlign: "center", width: 90, visible: false,
        formatter: "tickCross",
    },
    {
        title: "Quant", field: "quantization", sorter: "string",
        width: 80, visible: false,
    },
    {
        title: "Uptime", field: "uptime_pct", sorter: "number",
        hozAlign: "right", width: 80, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) + '%' : '—';
        },
    },
    {
        title: "TTFT p95", field: "ttft_p95_ms", sorter: "number",
        hozAlign: "right", width: 100, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "Tok/s p95", field: "tokens_per_sec_p95", sorter: "number",
        hozAlign: "right", width: 90, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "Requests", field: "recent_requests", sorter: "number",
        hozAlign: "right", width: 90, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toLocaleString() : '—';
        },
    },
    {
        title: "Benchmark", field: "benchmark_config", sorter: "string",
        width: 150, visible: false,
    },
];

export function createTable(containerEl, data) {
    table = new Tabulator(containerEl, {
        data: data,
        height: "100%",
        layout: "fitDataFill",
        groupBy: "model",
        groupStartOpen: true,
        groupToggleElement: "header",
        groupHeader: (value, count) => {
            return `<span style="font-weight:600">${value}</span> <span style="opacity:0.5">(${count} provider${count !== 1 ? 's' : ''})</span>`;
        },
        columns: COLUMNS,
        initialSort: [
            { column: "model", dir: "asc" },
            { column: "ttft_ms", dir: "asc" },
        ],
        placeholder: "No matching models",
    });
    return table;
}

export function updateTable(data) {
    if (table) {
        table.replaceData(data);
    }
}

export function getRowCount() {
    return table ? table.getDataCount() : 0;
}
```

- [ ] **Step 2: Commit**

```bash
git -c commit.gpgsign=false add site/table.js
git -c commit.gpgsign=false commit -m "feat: Tabulator table config with grouping and columns"
```

---

## Task 4: Facet Sidebar

**Files:**
- Create: `site/facets.js`

- [ ] **Step 1: Create facets.js**

```javascript
const CHECKBOX_FACETS = [
    { id: 'provider', title: 'Provider', column: 'provider' },
    { id: 'model_group', title: 'Model Family', column: 'model_group' },
];

const BOOLEAN_FACETS = [
    { id: 'reasoning', title: 'Reasoning', column: 'supports_reasoning', label: 'Reasoning models only' },
    { id: 'free', title: 'Free', column: 'is_free', label: 'Free models only' },
    { id: 'tools', title: 'Tools', column: 'tools_support', label: 'Tool calling support' },
];

const RANGE_FACETS = [
    { id: 'ttft', title: 'TTFT (ms)', column: 'ttft_ms', step: 10 },
    { id: 'throughput', title: 'Throughput (tok/s)', column: 'tokens_per_sec', step: 5 },
    { id: 'intelligence', title: 'Intelligence Index', column: 'intelligence_index', step: 0.5 },
    { id: 'coding', title: 'Coding Index', column: 'coding_index', step: 0.5 },
    { id: 'agentic', title: 'Agentic Index', column: 'agentic_index', step: 0.5 },
    { id: 'context', title: 'Context Length', column: 'context_length', step: 1000 },
    { id: 'price', title: 'Input Price ($/M)', column: 'input_price_per_m', step: 0.1 },
];

let facetState = {};
let onChange = null;

export async function initFacets(containerEl, queryFn, onChangeCb) {
    onChange = onChangeCb;
    containerEl.innerHTML = '';

    // Checkbox facets
    for (const facet of CHECKBOX_FACETS) {
        const values = await queryFn(
            `SELECT DISTINCT ${facet.column} FROM mega_view WHERE ${facet.column} IS NOT NULL ORDER BY ${facet.column}`
        );
        const group = document.createElement('div');
        group.className = 'facet-group';
        group.innerHTML = `<label class="facet-title">${facet.title}</label><div class="facet-options" id="facet-${facet.id}"></div>`;
        const optionsEl = group.querySelector('.facet-options');
        for (const row of values) {
            const val = row[facet.column];
            const label = document.createElement('label');
            label.innerHTML = `<input type="checkbox" data-facet="${facet.id}" value="${val}" checked> ${val}`;
            label.querySelector('input').addEventListener('change', _handleChange);
            optionsEl.appendChild(label);
        }
        containerEl.appendChild(group);
    }

    // Boolean facets
    for (const facet of BOOLEAN_FACETS) {
        const group = document.createElement('div');
        group.className = 'facet-group';
        group.innerHTML = `<label class="facet-title">${facet.title}</label>
            <div class="facet-options">
                <label><input type="checkbox" data-facet="${facet.id}"> ${facet.label}</label>
            </div>`;
        group.querySelector('input').addEventListener('change', _handleChange);
        containerEl.appendChild(group);
    }

    // Range facets
    for (const facet of RANGE_FACETS) {
        const stats = await queryFn(
            `SELECT MIN(${facet.column}) AS min_val, MAX(${facet.column}) AS max_val FROM mega_view WHERE ${facet.column} IS NOT NULL`
        );
        if (!stats.length || stats[0].min_val == null) continue;
        const min = Math.floor(stats[0].min_val);
        const max = Math.ceil(stats[0].max_val);
        facetState[facet.id] = { min, max, currentMin: min, currentMax: max };

        const group = document.createElement('div');
        group.className = 'facet-group';
        group.innerHTML = `<label class="facet-title">${facet.title}</label>
            <input type="range" id="facet-${facet.id}-min" min="${min}" max="${max}" value="${min}" step="${facet.step}">
            <input type="range" id="facet-${facet.id}-max" min="${min}" max="${max}" value="${max}" step="${facet.step}">
            <div class="range-values"><span id="facet-${facet.id}-min-label">${min}</span><span id="facet-${facet.id}-max-label">${max}</span></div>`;
        group.querySelectorAll('input[type=range]').forEach(el => {
            el.addEventListener('input', (e) => {
                const isMin = e.target.id.endsWith('-min');
                const label = document.getElementById(`facet-${facet.id}-${isMin ? 'min' : 'max'}-label`);
                label.textContent = e.target.value;
                _handleChange();
            });
        });
        containerEl.appendChild(group);
    }
}

function _handleChange() {
    if (onChange) onChange();
}

export function buildWhereClause() {
    const clauses = [];

    // Checkbox facets: only include checked values
    for (const facet of CHECKBOX_FACETS) {
        const checkboxes = document.querySelectorAll(`[data-facet="${facet.id}"]`);
        const allChecked = [...checkboxes].filter(cb => cb.checked).map(cb => cb.value);
        const allValues = [...checkboxes].map(cb => cb.value);
        if (allChecked.length < allValues.length && allChecked.length > 0) {
            const escaped = allChecked.map(v => `'${v.replace(/'/g, "''")}'`).join(', ');
            clauses.push(`${facet.column} IN (${escaped})`);
        } else if (allChecked.length === 0) {
            clauses.push('FALSE');
        }
    }

    // Boolean facets: only filter if checked
    for (const facet of BOOLEAN_FACETS) {
        const cb = document.querySelector(`[data-facet="${facet.id}"]`);
        if (cb && cb.checked) {
            clauses.push(`${facet.column} = TRUE`);
        }
    }

    // Range facets
    for (const facet of RANGE_FACETS) {
        const minEl = document.getElementById(`facet-${facet.id}-min`);
        const maxEl = document.getElementById(`facet-${facet.id}-max`);
        if (!minEl || !maxEl) continue;
        const state = facetState[facet.id];
        if (!state) continue;
        const curMin = parseFloat(minEl.value);
        const curMax = parseFloat(maxEl.value);
        if (curMin > state.min) {
            clauses.push(`${facet.column} >= ${curMin}`);
        }
        if (curMax < state.max) {
            clauses.push(`${facet.column} <= ${curMax}`);
        }
    }

    return clauses.length > 0 ? 'WHERE ' + clauses.join(' AND ') : '';
}
```

- [ ] **Step 2: Commit**

```bash
git -c commit.gpgsign=false add site/facets.js
git -c commit.gpgsign=false commit -m "feat: facet sidebar with checkboxes and range sliders"
```

---

## Task 5: SQL Tab

**Files:**
- Create: `site/sql-tab.js`

- [ ] **Step 1: Create sql-tab.js**

```javascript
let resultsTable = null;

export function initSqlTab(queryFn) {
    const runBtn = document.getElementById('sql-run');
    const input = document.getElementById('sql-input');
    const errorEl = document.getElementById('sql-error');

    async function runQuery() {
        errorEl.classList.add('hidden');
        const sql = input.value.trim();
        if (!sql) return;

        try {
            const rows = await queryFn(sql);
            if (rows.length === 0) {
                errorEl.textContent = 'Query returned 0 rows.';
                errorEl.classList.remove('hidden');
                if (resultsTable) resultsTable.destroy();
                resultsTable = null;
                return;
            }

            // Auto-generate columns from first row
            const columns = Object.keys(rows[0]).map(key => ({
                title: key,
                field: key,
                sorter: typeof rows[0][key] === 'number' ? 'number' : 'string',
                headerFilter: "input",
            }));

            if (resultsTable) resultsTable.destroy();
            resultsTable = new Tabulator('#sql-results', {
                data: rows,
                columns: columns,
                height: "100%",
                layout: "fitDataFill",
                placeholder: "No results",
            });
        } catch (e) {
            errorEl.textContent = e.message || String(e);
            errorEl.classList.remove('hidden');
        }
    }

    runBtn.addEventListener('click', runQuery);
    input.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runQuery();
        }
    });
}
```

- [ ] **Step 2: Commit**

```bash
git -c commit.gpgsign=false add site/sql-tab.js
git -c commit.gpgsign=false commit -m "feat: SQL tab with query execution and auto-column detection"
```

---

## Task 6: Main App — Wire Everything Together

**Files:**
- Create: `site/app.js`

- [ ] **Step 1: Create app.js**

```javascript
import { initDB, query } from './db.js';
import { initFacets, buildWhereClause } from './facets.js';
import { createTable, updateTable, getRowCount } from './table.js';
import { initSqlTab } from './sql-tab.js';

const MEGA_VIEW_SQL = `
SELECT
    m.name AS model,
    m.author,
    m.slug AS model_slug,
    m.context_length,
    m.supports_reasoning,
    m.group AS model_group,
    e.endpoint_id,
    e.provider_slug AS provider,
    e.quantization,
    e.variant,
    e.is_free,
    CAST(e.pricing_prompt AS DOUBLE) * 1000000 AS input_price_per_m,
    CAST(e.pricing_completion AS DOUBLE) * 1000000 AS output_price_per_m,
    e.latency_p50 AS ttft_ms,
    e.latency_p95 AS ttft_p95_ms,
    e.throughput_p50 AS tokens_per_sec,
    e.throughput_p95 AS tokens_per_sec_p95,
    e.uptime_30m AS uptime_pct,
    e.stats_request_count AS recent_requests,
    e.supports_tool_parameters AS tools_support,
    b.intelligence_index,
    b.coding_index,
    b.agentic_index,
    b.intelligence_percentile AS intelligence_pct,
    b.coding_percentile AS coding_pct,
    b.agentic_percentile AS agentic_pct,
    b.aa_name AS benchmark_config
FROM model_endpoints e
JOIN models m ON m.slug = e.model_slug
LEFT JOIN (
    SELECT * FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY model_slug
                ORDER BY
                    CASE
                        WHEN aa_name ILIKE '%medium%' THEN 1
                        WHEN aa_name ILIKE '%reasoning%'
                             AND aa_name NOT ILIKE '%non-reasoning%'
                             AND aa_name NOT ILIKE '%max%'
                             AND aa_name NOT ILIKE '%high%'
                             AND aa_name NOT ILIKE '%low%'
                             AND aa_name NOT ILIKE '%minimal%' THEN 2
                        WHEN aa_name NOT ILIKE '%non-reasoning%'
                             AND aa_name NOT ILIKE '%max%'
                             AND aa_name NOT ILIKE '%xhigh%' THEN 3
                        ELSE 4
                    END,
                    intelligence_index DESC NULLS LAST
            ) AS rn
        FROM model_benchmarks
        WHERE intelligence_index IS NOT NULL
    ) ranked WHERE rn = 1
) b ON b.model_slug = m.slug
`;

async function main() {
    const loadingEl = document.getElementById('loading');
    const statusBar = document.getElementById('status-bar');

    // Init DuckDB
    loadingEl.textContent = 'Downloading database...';
    await initDB('public/openrouter.duckdb');
    loadingEl.textContent = 'Creating view...';

    // Create the mega view
    await query(`CREATE OR REPLACE VIEW mega_view AS ${MEGA_VIEW_SQL}`);

    // Initial data load
    loadingEl.textContent = 'Loading data...';
    const initialData = await query('SELECT * FROM mega_view ORDER BY model, provider');
    loadingEl.classList.add('hidden');

    // Create table
    createTable('#table', initialData);
    statusBar.textContent = `${initialData.length} endpoints across ${new Set(initialData.map(r => r.model_slug)).size} models`;

    // Init facets
    const facetsEl = document.getElementById('facets');
    document.getElementById('facets-loading').remove();
    await initFacets(facetsEl, query, async () => {
        const where = buildWhereClause();
        const sql = `SELECT * FROM mega_view ${where} ORDER BY model, provider`;
        const rows = await query(sql);
        updateTable(rows);
        statusBar.textContent = `${rows.length} endpoints across ${new Set(rows.map(r => r.model_slug)).size} models`;
    });

    // Init SQL tab
    initSqlTab(query);

    // Tab switching
    const tabExplore = document.getElementById('tab-explore');
    const tabSql = document.getElementById('tab-sql');
    const viewExplore = document.getElementById('view-explore');
    const viewSql = document.getElementById('view-sql');

    tabExplore.addEventListener('click', () => {
        tabExplore.classList.add('active');
        tabSql.classList.remove('active');
        viewExplore.classList.remove('hidden');
        viewSql.classList.add('hidden');
    });

    tabSql.addEventListener('click', () => {
        tabSql.classList.add('active');
        tabExplore.classList.remove('active');
        viewSql.classList.remove('hidden');
        viewExplore.classList.add('hidden');
    });
}

main().catch(err => {
    document.getElementById('loading').textContent = `Error: ${err.message}`;
    console.error(err);
});
```

- [ ] **Step 2: Commit**

```bash
git -c commit.gpgsign=false add site/app.js
git -c commit.gpgsign=false commit -m "feat: main app wiring DuckDB, Tabulator, facets, and SQL tab"
```

---

## Task 7: Copy Database & Smoke Test

**Files:**
- Modify: `site/public/openrouter.duckdb` (copy from data/)
- Modify: `.gitignore`

- [ ] **Step 1: Copy the database**

```bash
mkdir -p site/public
cp data/openrouter.duckdb site/public/openrouter.duckdb
```

- [ ] **Step 2: Add site/public to .gitignore**

Append to `.gitignore`:
```
site/public/*.duckdb
```

- [ ] **Step 3: Serve and test locally**

```bash
python3 -m http.server 8000 -d site/
```

Open `http://localhost:8000` in a browser. Verify:
- Database loads (loading spinner disappears)
- Table renders with grouped rows (collapsible by model)
- Facet sidebar shows providers, sliders
- Clicking a facet checkbox re-filters the table
- SQL tab runs a query and shows results

- [ ] **Step 4: Fix any issues found during smoke test**

Common issues:
- CORS on DuckDB-WASM worker: ensure serving from `http://` not `file://`
- Tabulator column width issues: adjust `layout` or column widths
- DuckDB query errors: check SQL syntax in mega_view

- [ ] **Step 5: Commit**

```bash
git -c commit.gpgsign=false add site/ .gitignore
git -c commit.gpgsign=false commit -m "feat: complete model explorer with smoke test"
```

---

## Task 8: Deploy to Cloudflare Pages

- [ ] **Step 1: Create a build script**

Create `site/build.sh`:
```bash
#!/bin/bash
set -e
mkdir -p site/public
cp data/openrouter.duckdb site/public/openrouter.duckdb
echo "Build complete — site/ ready for deploy"
```

```bash
chmod +x site/build.sh
```

- [ ] **Step 2: Deploy via Cloudflare Pages**

Option A — via Wrangler CLI:
```bash
npx wrangler pages deploy site/ --project-name openrouter-explorer
```

Option B — via dashboard:
1. Go to Cloudflare Dashboard → Pages → Create project
2. Connect the GitHub repo
3. Build command: `bash site/build.sh`
4. Build output directory: `site/`

- [ ] **Step 3: Verify live site works**

Open the deployed URL. Verify same behavior as local smoke test.

- [ ] **Step 4: Commit build script**

```bash
git -c commit.gpgsign=false add site/build.sh
git -c commit.gpgsign=false commit -m "chore: add build script for Cloudflare Pages deploy"
```
