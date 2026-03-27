# OpenRouter Model Explorer — Design Spec

## Goal

A public, static website where anyone can explore, filter, sort, and compare OpenRouter models and their provider endpoints — without writing SQL. Optimized for use cases like "find the fastest model above X benchmark threshold" or "compare providers for a given model." Optionally exposes a raw SQL query box for power users.

## Stack

- **DuckDB-WASM** — runs the full DuckDB engine in the browser, loads a `.duckdb` file as a static asset
- **Tabulator** — MIT-licensed table library with built-in row grouping, collapsible groups, column sorting, filtering
- **Vanilla JS** (or minimal framework) — wire DuckDB queries to Tabulator and facet sidebar
- **Hosted on Cloudflare Pages** (or GitHub Pages / Netlify / Vercel) — all free static hosting

## Data Flow

```
Build time (scraper):
  OpenRouter APIs → scraper → data/openrouter.duckdb

Deploy time:
  openrouter.duckdb copied to site/public/ as static asset

Runtime (browser):
  1. Page loads → DuckDB-WASM initializes → loads openrouter.duckdb
  2. Runs pre-joined SQL view → flat result set
  3. Tabulator renders the table
  4. Facet sidebar populated from DISTINCT queries
  5. User filters/sorts → re-query DuckDB → update Tabulator
```

## Pre-Joined View

A single SQL view materializes at page load, joining models + endpoints + benchmarks into one flat table. This is what the user sees — no knowledge of the underlying schema needed.

```sql
SELECT
    m.name AS model,
    m.author,
    m.slug AS model_slug,
    m.context_length,
    m.supports_reasoning,
    m.group AS model_group,
    m.input_modalities,
    m.output_modalities,
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
    e.context_length AS endpoint_context_length,
    e.max_completion_tokens,
    e.supported_parameters,
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
    -- Pick the "average" benchmark config per model:
    -- prefer "medium" effort, then "Reasoning" without qualifier,
    -- then the entry closest to the median intelligence_index
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
WHERE e.latency_p50 IS NOT NULL OR b.intelligence_index IS NOT NULL
ORDER BY m.name, e.provider_slug
```

This produces ~800-900 rows (endpoints with at least perf data or benchmarks), one row per model×provider, with benchmark scores flattened in.

## UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  OpenRouter Model Explorer                          [SQL] tab   │
├────────────────┬────────────────────────────────────────────────┤
│ FILTERS        │  TABLE                                         │
│                │                                                │
│ ☐ Provider     │  Model  Provider  TTFT  Tok/s  Intel  Code ... │
│   ☐ Anthropic  │  ─────────────────────────────────────────     │
│   ☐ Google     │  ▼ Claude Sonnet 4.6                           │
│   ☐ OpenAI     │    Anthropic   1259ms  47/s   51.7   50.9     │
│   ☐ Groq       │    Google      1075ms  44/s   51.7   50.9     │
│   ...          │    Bedrock     1895ms  37/s   51.7   50.9     │
│                │  ▼ GPT-4o                                      │
│ Reasoning      │    OpenAI       548ms  48/s   18.6   16.6     │
│   ☐ Yes ☐ No   │    Azure       4276ms  24/s   18.6   16.6     │
│                │  ▶ Qwen3 32B  (collapsed)                      │
│ TTFT (ms)      │  ▶ Llama 3.3  (collapsed)                     │
│ [0━━━━━5000]   │                                                │
│                │                                                │
│ Throughput     │                                                │
│ [0━━━━━1000]   │                                                │
│                │                                                │
│ Intel Index    │                                                │
│ [0━━━━━60]     │                                                │
│                │                                                │
│ Context (k)    │                                                │
│ [0━━━━━2000]   │                                                │
│                │                                                │
│ Price ($/M in) │                                                │
│ [0━━━━━100]    │                                                │
│                │                                                │
│ Free only ☐    │                                                │
│ Tools ☐        │                                                │
└────────────────┴────────────────────────────────────────────────┘
```

## Table Features (via Tabulator)

- **Row grouping by model** — rows grouped by `model_slug`, group headers show model name, collapsible
- **Column sorting** — click any column header
- **Column header filters** — text search on string columns, numeric filters on numeric columns
- **Default sort** — by model name, then provider
- **Responsive** — horizontal scroll on narrow screens, frozen model/provider columns
- **Default visible columns** — model, provider, TTFT, tok/s, input price, intelligence/coding/agentic index
- **Hidden by default** (toggleable) — quantization, variant, uptime, p95 values, context length, max tokens, supported_parameters, benchmark_config

## Facet Sidebar

Built with plain HTML inputs, wired to DuckDB queries:

| Facet | Type | DuckDB query |
|---|---|---|
| Provider | Checkbox list | `SELECT DISTINCT provider FROM mega_view ORDER BY provider` |
| Reasoning | Checkbox (Yes/No) | Boolean filter on `supports_reasoning` |
| Model Group | Checkbox list | `SELECT DISTINCT model_group FROM mega_view` |
| TTFT (ms) | Range slider | `SELECT MIN(ttft_ms), MAX(ttft_ms) FROM mega_view` |
| Throughput (tok/s) | Range slider | min/max query |
| Intelligence Index | Range slider | min/max query |
| Coding Index | Range slider | min/max query |
| Agentic Index | Range slider | min/max query |
| Context Length | Range slider | min/max query |
| Input Price ($/M) | Range slider | min/max query |
| Free Only | Checkbox | Boolean filter on `is_free` |
| Tools Support | Checkbox | Boolean filter on `tools_support` |

When any facet changes, rebuild the `WHERE` clause and re-query DuckDB. Tabulator updates via `table.replaceData(newRows)`.

## SQL Tab (Optional Power User Feature)

A secondary tab with:
- CodeMirror or a `<textarea>` for SQL input
- "Run" button executes against DuckDB-WASM
- Results rendered in a plain Tabulator table
- Pre-populated with a helpful example query
- Access to all underlying tables (models, model_endpoints, providers, model_benchmarks, model_analytics, model_categories)

## File Structure

```
site/
├── index.html          — single page app shell
├── style.css           — layout, facet sidebar, table styling
├── app.js              — main: init DuckDB, wire facets, render table
├── db.js               — DuckDB-WASM init, query helpers
├── facets.js           — facet sidebar: render, read state, build WHERE
├── sql-tab.js          — optional SQL editor tab
└── public/
    └── openrouter.duckdb  — static database file (~5MB)
```

## Build & Deploy

The scraper already produces `data/openrouter.duckdb`. The deploy pipeline:

1. `uv run scrape` — refresh the database
2. Copy `data/openrouter.duckdb` to `site/public/`
3. Deploy `site/` to Cloudflare Pages (or GitHub Pages)

For Cloudflare Pages: connect the repo, set build command to a simple copy script, publish directory `site/`.

For GitHub Pages: GitHub Action that runs the scraper on a schedule, commits the `.duckdb` file, deploys `site/` via `gh-pages` branch.

## Performance Budget

- DuckDB-WASM: ~4MB (gzipped ~1.5MB)
- Tabulator: ~100KB (gzipped ~30KB)
- openrouter.duckdb: ~5MB (gzipped ~2MB)
- Total first load: ~8MB → ~3.5MB gzipped
- DuckDB init + first query: < 2s on broadband
- Subsequent filter queries: < 100ms (in-memory)

## Out of Scope

- User accounts, saved queries, sharing URLs (can add later via URL query params)
- Charts/visualizations (Tabulator table is the primary interface)
- Real-time data updates (scraper runs on-demand or scheduled, site is static)
- Mobile-optimized layout (responsive but not mobile-first)
