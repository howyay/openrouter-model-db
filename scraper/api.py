"""Fetch model data from OpenRouter public API and model pages."""

import asyncio
import httpx

BASE_URL = "https://openrouter.ai"
CONCURRENCY_LIMIT = 10
REQUEST_DELAY = 0.1


def _auth_headers(api_key: str | None) -> dict[str, str]:
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    return {}


async def fetch_model_list(client: httpx.AsyncClient) -> list[dict]:
    """Fetch all models from /api/v1/models. Returns the 'data' array."""
    resp = await client.get(f"{BASE_URL}/api/v1/models")
    resp.raise_for_status()
    return resp.json()["data"]


async def fetch_model_endpoints(
    client: httpx.AsyncClient, slug: str, api_key: str | None = None
) -> dict | None:
    """Fetch endpoint details (with latency/throughput if authenticated).

    Returns the 'data' object or None on failure.
    """
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/models/{slug}/endpoints",
            headers=_auth_headers(api_key),
        )
        resp.raise_for_status()
        return resp.json().get("data")
    except (httpx.HTTPStatusError, httpx.RequestError):
        return None


async def fetch_all_model_endpoints(
    client: httpx.AsyncClient,
    slugs: list[str],
    api_key: str | None = None,
    concurrency: int = CONCURRENCY_LIMIT,
    delay: float = REQUEST_DELAY,
    on_progress: callable = None,
) -> dict[str, dict]:
    """Fetch endpoint data for all models with bounded concurrency.

    Returns dict mapping slug -> endpoints API response.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, dict] = {}
    completed = 0

    async def _fetch_one(slug: str):
        nonlocal completed
        async with semaphore:
            data = await fetch_model_endpoints(client, slug, api_key)
            if data:
                results[slug] = data
            completed += 1
            if on_progress:
                on_progress(completed, len(slugs), slug)
            await asyncio.sleep(delay)

    tasks = [_fetch_one(slug) for slug in slugs]
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
    on_progress: callable = None,
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
