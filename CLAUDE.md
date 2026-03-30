# OpenRouter Model Database

Scrapes all OpenRouter model pages and produces a DuckDB database with a Svelte explorer UI.

## Package Management

Always use `uv` instead of `pip`. Never run `pip install` directly.

- Install dependencies: `uv sync`
- Add a dependency: `uv add <package>`
- Run the scraper: `uv run scrape`
- Run tests: `uv run pytest`

## Project Structure

- `scraper/` — Python package with the scraping pipeline
  - `api.py` — async HTTP client for OpenRouter API
  - `rsc.py` — Next.js RSC payload extractor from HTML
  - `transform.py` — nested JSON to flat row dicts
  - `db.py` — DuckDB writer
  - `main.py` — orchestrator: fetch all → transform → write
- `site/` — Svelte + Vite frontend (explorer UI)
  - `src/App.svelte` — main app with tabs (Explore / SQL)
  - `src/components/` — Sidebar, DataTable, facet components
  - `src/lib/db.js` — DuckDB-WASM client
  - `src/lib/facets.js` — facet definitions and SQL builder
- `data/` — output DuckDB database (gitignored)
- `queries/examples.sql` — example DuckDB queries
- `docker-compose.yml` — Apache Superset with DuckDB support

## Running

```bash
uv run scrape                    # full scrape pipeline
uv run pytest                    # run tests
cd site && npm install           # install site deps
cd site && npm run dev           # dev server (Vite)
cd site && npm run build         # production build -> site/dist/
podman compose up -d             # start Superset on port 18630
```

## Git

Use `git -c commit.gpgsign=false` for commits (GPG agent not available in this environment).
