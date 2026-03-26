# OpenRouter Model Database

Scrapes all OpenRouter model pages and produces Parquet files queryable via DuckDB, agx, and Apache Superset.

## Package Management

Always use `uv` instead of `pip`. Never run `pip install` directly.

- Install dependencies: `uv sync`
- Install with dev deps: `uv sync --dev`
- Add a dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
- Run a script: `uv run <command>`
- Run the scraper: `uv run scrape`
- Run tests: `uv run pytest`

## Project Structure

- `scraper/` — Python package with the scraping pipeline
  - `api.py` — async HTTP client for OpenRouter API
  - `rsc.py` — Next.js RSC payload extractor from HTML
  - `benchmarks.py` — regex benchmark extractor from descriptions
  - `transform.py` — nested JSON to flat row dicts
  - `parquet.py` — PyArrow schemas and Parquet writers
  - `main.py` — orchestrator: fetch all → transform → write
- `data/` — output Parquet files (gitignored)
- `queries/examples.sql` — example DuckDB queries
- `docker-compose.yml` — Apache Superset with DuckDB support

## Running

```bash
uv run scrape                    # full scrape pipeline
uv run pytest                    # run tests
podman compose up -d             # start Superset on port 18630
```

## Git

Use `git -c commit.gpgsign=false` for commits (GPG agent not available in this environment).
