"""Main orchestrator: fetch all models -> transform -> write DuckDB database."""

import asyncio
from pathlib import Path

import httpx

from scraper.api import fetch_model_list, fetch_all_model_pages
from scraper.rsc import extract_rsc_model_data, extract_rsc_categories
from scraper.benchmarks import extract_benchmarks
from scraper.transform import (
    transform_model,
    transform_endpoints,
    transform_provider,
    transform_analytics,
    transform_categories,
)
from scraper.db import write_all

DATA_DIR = Path(__file__).parent.parent / "data"


def _progress(completed: int, total: int, slug: str):
    print(f"\r  [{completed}/{total}] {slug[:50]:<50}", end="", flush=True)


async def scrape(output_dir: Path = DATA_DIR, concurrency: int = 10, delay: float = 0.1):
    """Run the full scraping pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("1. Fetching model list from API...")
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        api_models = await fetch_model_list(client)

    slugs = [m["id"] for m in api_models]
    print(f"   Found {len(slugs)} models")

    print("2. Fetching model pages...")
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        pages = await fetch_all_model_pages(
            client, slugs, concurrency=concurrency, delay=delay, on_progress=_progress
        )
    print(f"\n   Fetched {len(pages)} pages")

    # Build lookup from API data
    api_lookup = {m["id"]: m for m in api_models}

    # Accumulators
    all_models = []
    all_endpoints = []
    all_providers = {}  # keyed by slug for dedup
    all_benchmarks = []
    all_analytics = []
    all_categories = []
    skipped = 0

    print("3. Transforming data...")
    for slug, html in pages.items():
        rsc_data = extract_rsc_model_data(html)
        if rsc_data is None:
            skipped += 1
            continue

        # Models
        model_row = transform_model(rsc_data)
        # Supplement with API data (tokenizer, instruct_type)
        api_model = api_lookup.get(slug, {})
        arch = api_model.get("architecture") or {}
        if not model_row.get("tokenizer"):
            model_row["tokenizer"] = arch.get("tokenizer")
        if not model_row.get("instruct_type"):
            model_row["instruct_type"] = arch.get("instruct_type")
        all_models.append(model_row)

        # Endpoints
        all_endpoints.extend(transform_endpoints(rsc_data))

        # Provider (deduplicated)
        provider_row = transform_provider(rsc_data)
        if provider_row and provider_row["slug"] not in all_providers:
            all_providers[provider_row["slug"]] = provider_row

        # Benchmarks
        description = rsc_data["model"].get("description", "")
        for bm in extract_benchmarks(description):
            bm["model_slug"] = slug
            bm["source"] = "description"
            all_benchmarks.append(bm)

        # Analytics
        all_analytics.extend(transform_analytics(rsc_data))

        # Categories
        rsc_categories = extract_rsc_categories(html)
        all_categories.extend(transform_categories(slug, rsc_categories))

    print(f"   Processed {len(all_models)} models, skipped {skipped}")
    print(f"   {len(all_endpoints)} endpoints, {len(all_providers)} providers")
    print(f"   {len(all_benchmarks)} benchmarks, {len(all_analytics)} analytics rows")
    print(f"   {len(all_categories)} category rows")

    db_path = str(output_dir / "openrouter.duckdb")
    print(f"4. Writing DuckDB database to {db_path}...")
    write_all(db_path, {
        "models": all_models,
        "model_endpoints": all_endpoints,
        "providers": list(all_providers.values()),
        "model_benchmarks": all_benchmarks,
        "model_analytics": all_analytics,
        "model_categories": all_categories,
    })
    print("   Done.")


def cli():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Scrape OpenRouter model data to DuckDB")
    parser.add_argument("-o", "--output", default=str(DATA_DIR), help="Output directory")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Max concurrent requests")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="Delay between requests (seconds)")
    args = parser.parse_args()
    asyncio.run(scrape(output_dir=Path(args.output), concurrency=args.concurrency, delay=args.delay))


if __name__ == "__main__":
    cli()
