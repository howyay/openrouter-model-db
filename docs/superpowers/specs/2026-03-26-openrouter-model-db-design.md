# OpenRouter Model Database — Design Spec

## Goal

Build a local, SQL-queryable database of all OpenRouter model metadata — including provider details, pricing, benchmarks, analytics, and category rankings. Output as Parquet files for use with DuckDB (primary), agx (bundled ClickHouse), Apache Superset, and clickhouse-local.

## Data Sources

### 1. Public API (structured, reliable)

- `GET /api/v1/models` — list of all models with core metadata, pricing, supported parameters, defaults
- `GET /api/v1/models/{author}/{slug}/endpoints` — per-model endpoint list with provider name, quantization, latency/throughput/uptime, pricing, supported params

### 2. RSC Payload (rich, extracted from HTML)

Each model page at `https://openrouter.ai/{author}/{slug}` embeds a full JSON object in the Next.js RSC flight data (`self.__next_f.push(...)` script tags). This contains everything the API provides plus:

- Provider info (HQ, data centers, data policy, BYOK, terms/privacy URLs, adapter name)
- Long-context pricing tiers (threshold, above-threshold prices)
- Daily analytics (requests, tokens, tool calls, errors, cache hits) — ~8 days of history
- Use case category rankings (category, rank, volume, token counts)
- Reasoning configuration (start/end tokens, return mechanism)
- Feature support details (tool choice modes, multipart support)
- Warning/promotion messages

### Benchmark extraction

Benchmarks are embedded in free-text `description` fields (e.g., "SWE-bench (72.5%)"). These are extracted via regex into structured rows. This is inherently lossy — not all models have benchmarks, and formats vary.

## Data Model

Six tables, stored as individual Parquet files.

### `models.parquet`

| Column | Type | Source | Notes |
|---|---|---|---|
| slug | VARCHAR (PK) | API+RSC | e.g. `anthropic/claude-opus-4` |
| name | VARCHAR | API | e.g. `Anthropic: Claude Opus 4` |
| short_name | VARCHAR | RSC | e.g. `Claude Opus 4` |
| author | VARCHAR | RSC | e.g. `anthropic` |
| description | VARCHAR | API | full markdown text |
| context_length | INTEGER | API | max input tokens |
| group | VARCHAR | RSC | e.g. `Claude`, `GPT`, `Other` |
| input_modalities | VARCHAR[] | API | e.g. `['text', 'image']` |
| output_modalities | VARCHAR[] | API | e.g. `['text']` |
| supports_reasoning | BOOLEAN | RSC | |
| knowledge_cutoff | TIMESTAMP | API | nullable |
| permaslug | VARCHAR | RSC | versioned slug |
| hf_slug | VARCHAR | RSC | HuggingFace model ID |
| created_at | TIMESTAMP | RSC | |
| updated_at | TIMESTAMP | RSC | |
| warning_message | VARCHAR | RSC | nullable |
| default_temperature | DOUBLE | API | nullable |
| default_top_p | DOUBLE | API | nullable |
| default_top_k | INTEGER | API | nullable |
| default_frequency_penalty | DOUBLE | API | nullable |
| default_presence_penalty | DOUBLE | API | nullable |
| default_repetition_penalty | DOUBLE | API | nullable |
| instruct_type | VARCHAR | API | nullable |
| tokenizer | VARCHAR | API | e.g. `Claude`, `GPT`, `Other` |
| scraped_at | TIMESTAMP | scraper | when this row was collected |

### `model_endpoints.parquet`

| Column | Type | Source | Notes |
|---|---|---|---|
| endpoint_id | VARCHAR (PK) | RSC | UUID |
| model_slug | VARCHAR (FK) | RSC | |
| provider_slug | VARCHAR (FK) | RSC | e.g. `anthropic`, `google-vertex` |
| endpoint_name | VARCHAR | RSC | e.g. `Anthropic \| anthropic/claude-4-opus-20250522` |
| quantization | VARCHAR | API+RSC | e.g. `fp8`, `fp16`, null |
| variant | VARCHAR | RSC | e.g. `standard`, `extended` |
| context_length | INTEGER | RSC | provider-specific context length |
| max_completion_tokens | INTEGER | RSC | |
| max_prompt_tokens | INTEGER | RSC | nullable |
| pricing_prompt | DECIMAL(18,12) | RSC | USD per token |
| pricing_completion | DECIMAL(18,12) | RSC | USD per token |
| pricing_cache_read | DECIMAL(18,12) | RSC | nullable |
| pricing_cache_write | DECIMAL(18,12) | RSC | nullable |
| pricing_image | DECIMAL(18,12) | RSC | nullable |
| pricing_web_search | DECIMAL(18,12) | RSC | nullable |
| pricing_discount | DOUBLE | RSC | 0-1 |
| long_ctx_threshold | INTEGER | RSC | nullable, token count |
| long_ctx_prompt_price | DECIMAL(18,12) | RSC | nullable |
| long_ctx_completion_price | DECIMAL(18,12) | RSC | nullable |
| long_ctx_cache_read_price | DECIMAL(18,12) | RSC | nullable |
| uptime_30m | DOUBLE | API | percentage, nullable |
| latency_30m | DOUBLE | API | ms, nullable |
| throughput_30m | DOUBLE | API | tokens/sec, nullable |
| is_moderated | BOOLEAN | RSC | |
| is_byok | BOOLEAN | RSC | |
| is_free | BOOLEAN | RSC | |
| supported_parameters | VARCHAR[] | RSC | e.g. `['tools', 'reasoning', ...]` |
| supports_tool_parameters | BOOLEAN | RSC | |
| supports_reasoning | BOOLEAN | RSC | |
| supports_multipart | BOOLEAN | RSC | |
| provider_region | VARCHAR | RSC | nullable |
| scraped_at | TIMESTAMP | scraper | |

### `providers.parquet`

| Column | Type | Source | Notes |
|---|---|---|---|
| slug | VARCHAR (PK) | RSC | e.g. `anthropic`, `google-vertex` |
| name | VARCHAR | RSC | display name |
| base_url | VARCHAR | RSC | API base URL |
| headquarters | VARCHAR | RSC | ISO country code |
| datacenters | VARCHAR[] | RSC | ISO country codes |
| training | BOOLEAN | RSC | uses data for training |
| training_openrouter | BOOLEAN | RSC | OpenRouter trains on data |
| retains_prompts | BOOLEAN | RSC | |
| retention_days | INTEGER | RSC | nullable |
| can_publish | BOOLEAN | RSC | |
| requires_user_ids | BOOLEAN | RSC | |
| terms_url | VARCHAR | RSC | |
| privacy_url | VARCHAR | RSC | |
| byok_enabled | BOOLEAN | RSC | |
| is_abortable | BOOLEAN | RSC | |
| moderation_required | BOOLEAN | RSC | |
| adapter_name | VARCHAR | RSC | e.g. `XiaomiAdapter` |
| status_page_url | VARCHAR | RSC | nullable |
| scraped_at | TIMESTAMP | scraper | |

### `model_benchmarks.parquet`

| Column | Type | Notes |
|---|---|---|
| model_slug | VARCHAR (FK) | |
| benchmark_name | VARCHAR | e.g. `SWE-bench`, `Terminal-bench` |
| score | DOUBLE | e.g. `72.5` |
| unit | VARCHAR | e.g. `%`, `score`, `elo` |
| source | VARCHAR | `description` (extracted from text) |

Composite PK: `(model_slug, benchmark_name)`

Extraction regex patterns (applied to `description`):
- `(\w[\w\s-]+?)\s*\((\d+\.?\d*)%\)` — e.g. "SWE-bench (72.5%)"
- `(\w[\w\s-]+?):\s*(\d+\.?\d*)%` — e.g. "MMLU: 89.3%"
- Additional patterns can be added as new formats are discovered

### `model_analytics.parquet`

| Column | Type | Source | Notes |
|---|---|---|---|
| model_slug | VARCHAR (FK) | RSC | |
| date | DATE | RSC | |
| request_count | BIGINT | RSC | |
| completion_tokens | BIGINT | RSC | |
| prompt_tokens | BIGINT | RSC | |
| reasoning_tokens | BIGINT | RSC | |
| cached_tokens | BIGINT | RSC | |
| tool_calls | BIGINT | RSC | |
| tool_call_errors | BIGINT | RSC | |
| media_prompt_count | INTEGER | RSC | |
| media_completion_count | INTEGER | RSC | |
| audio_prompt_count | INTEGER | RSC | |

Composite PK: `(model_slug, date)`

### `model_categories.parquet`

| Column | Type | Source | Notes |
|---|---|---|---|
| model_slug | VARCHAR (FK) | RSC | |
| date | DATE | RSC | |
| category | VARCHAR | RSC | e.g. `programming`, `technology` |
| rank | INTEGER | RSC | ranking within category |
| volume | DOUBLE | RSC | usage volume metric |
| request_count | INTEGER | RSC | |
| prompt_tokens | BIGINT | RSC | |
| completion_tokens | BIGINT | RSC | |

Composite PK: `(model_slug, date, category)`

## Architecture

```
openrouter-model-db/
├── scraper/
│   ├── __init__.py
│   ├── api.py          # Public API fetcher (/api/v1/models, /endpoints)
│   ├── rsc.py          # RSC payload parser (HTML → JSON extraction)
│   ├── benchmarks.py   # Regex benchmark extractor from descriptions
│   ├── transform.py    # JSON → flat table rows
│   └── main.py         # Orchestrator: fetch all → transform → write parquet
├── data/
│   ├── models.parquet
│   ├── model_endpoints.parquet
│   ├── providers.parquet
│   ├── model_benchmarks.parquet
│   ├── model_analytics.parquet
│   └── model_categories.parquet
├── queries/            # Example SQL queries
│   └── examples.sql
└── pyproject.toml
```

### Scraping pipeline

1. **Fetch model list** from `/api/v1/models` → get all model slugs
2. **For each model**, fetch the HTML page and extract the RSC JSON payload
3. **Merge** API data + RSC data per model
4. **Extract benchmarks** from description text via regex
5. **Deduplicate providers** across all models
6. **Write** six Parquet files to `data/`

### Concurrency

- API calls: simple `httpx` async client, respect rate limits
- HTML fetches: async with concurrency limit (e.g., 10 at a time) to avoid hammering the server
- No stealth/Scrapling needed — we're fetching public HTML pages with standard HTTP, same as a browser loading the page. If rate-limited, add delays.

### Dependencies

- `httpx` — async HTTP client
- `pyarrow` — Parquet writer
- `polars` or `pandas` — optional, for DataFrame convenience
- Python 3.11+

No Scrapling needed for the current approach. The RSC payload is in plain HTML, no JS execution required.

## Querying

### DuckDB CLI
```sql
SELECT * FROM 'data/models.parquet' WHERE context_length >= 200000;
```

### agx
Drag and drop Parquet files, or:
```sql
SELECT * FROM file('data/models.parquet', Parquet) WHERE context_length >= 200000;
```

### Cross-table joins
```sql
SELECT m.name, e.provider_slug, e.pricing_prompt * 1000000 as price_per_m_input,
       e.latency_30m, e.throughput_30m
FROM 'data/models.parquet' m
JOIN 'data/model_endpoints.parquet' e ON m.slug = e.model_slug
WHERE m.supports_reasoning = true
ORDER BY e.pricing_prompt ASC;
```

### Benchmark comparison
```sql
SELECT m.name, b.benchmark_name, b.score
FROM 'data/model_benchmarks.parquet' b
JOIN 'data/models.parquet' m ON m.slug = b.model_slug
WHERE b.benchmark_name = 'SWE-bench'
ORDER BY b.score DESC;
```

## Backlog (Tier C)

Not in scope for initial build, but designed to accommodate later:

- **Full analytics history** — currently only ~8 days from RSC. Could run scraper on a cron to accumulate history over time.
- **Structured benchmark data** — if OpenRouter ever adds a benchmarks API or structured field
- **Superset dashboard** — pre-built dashboards for model comparison
- **Incremental updates** — only re-scrape models that changed (use `updated_at` as signal)
- **Delta/append mode** for analytics — append new daily rows instead of overwriting
