"""Fetch model data from OpenRouter public API and model pages."""

import asyncio
import httpx

BASE_URL = "https://openrouter.ai"
CONCURRENCY_LIMIT = 10
REQUEST_DELAY = 0.1


async def fetch_model_list(client: httpx.AsyncClient) -> list[dict]:
    """Fetch all models from /api/v1/models. Returns the 'data' array."""
    resp = await client.get(f"{BASE_URL}/api/v1/models")
    resp.raise_for_status()
    return resp.json()["data"]


async def fetch_endpoint_stats(
    client: httpx.AsyncClient, permaslug: str, variant: str = "standard"
) -> list[dict]:
    """Fetch latency/throughput percentile stats from the frontend stats API.

    Public endpoint, no auth needed. Returns list of endpoint stat dicts with
    keys like p50_latency, p50_throughput, endpoint_id, etc.
    """
    try:
        resp = await client.get(
            f"{BASE_URL}/api/frontend/stats/endpoint",
            params={"permaslug": permaslug, "variant": variant},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        results = []
        for ep in data if isinstance(data, list) else [data]:
            if isinstance(ep, dict) and "stats" in ep:
                stats = ep["stats"]
                stats["endpoint_id"] = ep.get("id")
                stats["endpoint_name"] = ep.get("name")
                results.append(stats)
        return results
    except (httpx.HTTPStatusError, httpx.RequestError):
        return []


async def fetch_all_endpoint_stats(
    client: httpx.AsyncClient,
    models: list[dict],
    concurrency: int = CONCURRENCY_LIMIT,
    delay: float = REQUEST_DELAY,
    on_progress=None,
) -> dict[str, list[dict]]:
    """Fetch endpoint stats for all models.

    Args:
        models: list of dicts with 'slug' and 'permaslug' keys.

    Returns dict mapping model slug -> list of endpoint stat dicts.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, list[dict]] = {}
    completed = 0

    async def _fetch_one(slug: str, permaslug: str):
        nonlocal completed
        async with semaphore:
            stats = await fetch_endpoint_stats(client, permaslug)
            if stats:
                results[slug] = stats
            completed += 1
            if on_progress:
                on_progress(completed, len(models), slug)
            await asyncio.sleep(delay)

    tasks = [
        _fetch_one(m["slug"], m["permaslug"])
        for m in models if m.get("permaslug")
    ]
    await asyncio.gather(*tasks)
    return results


async def fetch_benchmarks(
    client: httpx.AsyncClient, slug: str
) -> list[dict]:
    """Fetch Artificial Analysis benchmark data for a model.

    Uses the internal benchmarks API with the model's slug or permaslug.
    Returns list of benchmark entries (usually 0-1 items).
    """
    try:
        resp = await client.get(
            f"{BASE_URL}/api/internal/v1/artificial-analysis-benchmarks",
            params={"slug": slug},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    except (httpx.HTTPStatusError, httpx.RequestError):
        return []


async def fetch_all_benchmarks(
    client: httpx.AsyncClient,
    models: list[dict],
    concurrency: int = CONCURRENCY_LIMIT,
    delay: float = REQUEST_DELAY,
    on_progress=None,
) -> dict[str, list[dict]]:
    """Fetch benchmark data for all models, trying permaslug then slug.

    Returns dict mapping model slug -> list of benchmark entries.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, list[dict]] = {}
    completed = 0

    async def _fetch_one(slug: str, permaslug: str):
        nonlocal completed
        async with semaphore:
            # Try permaslug first (more specific), fallback to slug
            data = await fetch_benchmarks(client, permaslug)
            if not data:
                data = await fetch_benchmarks(client, slug)
            if data:
                results[slug] = data
            completed += 1
            if on_progress:
                on_progress(completed, len(models), slug)
            await asyncio.sleep(delay)

    tasks = [
        _fetch_one(m["slug"], m["permaslug"])
        for m in models if m.get("permaslug")
    ]
    await asyncio.gather(*tasks)
    return results


async def fetch_model_page(client: httpx.AsyncClient, slug: str) -> str:
    """Fetch the HTML of a model page. Returns raw HTML string."""
    resp = await client.get(f"{BASE_URL}/{slug}")
    resp.raise_for_status()
    return resp.text


async def fetch_all_model_pages(
    client: httpx.AsyncClient,
    slugs: list[str],
    concurrency: int = CONCURRENCY_LIMIT,
    delay: float = REQUEST_DELAY,
    on_progress=None,
) -> dict[str, str]:
    """Fetch HTML pages for all model slugs with bounded concurrency.

    Returns dict mapping slug -> HTML string.
    Failed fetches are skipped with a warning printed to stderr.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, str] = {}
    completed = 0

    async def _fetch_one(slug: str):
        nonlocal completed
        async with semaphore:
            try:
                html = await fetch_model_page(client, slug)
                results[slug] = html
            except httpx.HTTPStatusError as e:
                print(f"  WARN: {slug} returned {e.response.status_code}, skipping")
            except httpx.RequestError as e:
                print(f"  WARN: {slug} request failed: {e}, skipping")
            finally:
                completed += 1
                if on_progress:
                    on_progress(completed, len(slugs), slug)
                await asyncio.sleep(delay)

    tasks = [_fetch_one(slug) for slug in slugs]
    await asyncio.gather(*tasks)
    return results
