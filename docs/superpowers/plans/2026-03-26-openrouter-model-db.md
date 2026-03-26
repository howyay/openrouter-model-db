# OpenRouter Model Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape all OpenRouter model pages and produce six Parquet files queryable via DuckDB, agx, and clickhouse-local.

**Architecture:** Python async scraper that (1) fetches the model list from the public API, (2) fetches each model's HTML page to extract the rich RSC JSON payload, (3) transforms the nested JSON into flat table rows, and (4) writes six Parquet files. No database server — just files.

**Tech Stack:** Python 3.11+, httpx (async HTTP), pyarrow (Parquet), asyncio

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, dependencies |
| `scraper/__init__.py` | Package marker |
| `scraper/api.py` | Fetch model list from `/api/v1/models` |
| `scraper/rsc.py` | Fetch model HTML page, extract RSC JSON payload |
| `scraper/benchmarks.py` | Extract benchmark scores from description text via regex |
| `scraper/transform.py` | Convert raw JSON dicts into flat row dicts for each table |
| `scraper/parquet.py` | Define PyArrow schemas, write row dicts to Parquet files |
| `scraper/main.py` | Async orchestrator: fetch all → transform → write |
| `tests/test_rsc.py` | Tests for RSC payload extraction |
| `tests/test_benchmarks.py` | Tests for benchmark regex extraction |
| `tests/test_transform.py` | Tests for JSON → flat row transformation |
| `tests/test_parquet.py` | Tests for Parquet schema and write/read round-trip |
| `tests/conftest.py` | Shared fixtures (sample RSC JSON, sample API response) |
| `queries/examples.sql` | Example DuckDB queries |

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `scraper/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "openrouter-model-db"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "pyarrow>=18.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]

[project.scripts]
scrape = "scraper.main:cli"
```

- [ ] **Step 2: Create package markers**

Create `scraper/__init__.py` — empty file.
Create `tests/__init__.py` — empty file.

- [ ] **Step 3: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: installs httpx, pyarrow, pytest, pytest-asyncio

- [ ] **Step 4: Verify setup**

Run: `python -c "import httpx, pyarrow; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml scraper/__init__.py tests/__init__.py
git commit -m "chore: project setup with dependencies"
```

---

## Task 2: RSC Payload Extractor

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_rsc.py`
- Create: `scraper/rsc.py`

This is the core novelty — parsing the Next.js RSC flight data from HTML.

- [ ] **Step 1: Create test fixtures in conftest.py**

```python
import pytest

# Minimal HTML that mimics the OpenRouter model page RSC payload structure.
# The real page has many __next_f.push calls; we only need the one containing
# the model JSON (identified by "model":{"slug":...).
SAMPLE_RSC_HTML = r'''
<html><body>
<script>self.__next_f.push([1,"0:{\"P\":null}\n"])</script>
<script>self.__next_f.push([1,"3e:[\"$\",\"$L42\",null,{\"model\":{\"slug\":\"test/model-1\",\"hf_slug\":\"test-org/model-1\",\"updated_at\":\"2026-03-25T15:39:42.591683+00:00\",\"created_at\":\"2026-03-18T19:54:03.793004+00:00\",\"hf_updated_at\":null,\"name\":\"Test: Model-1\",\"short_name\":\"Model-1\",\"author\":\"test\",\"description\":\"A test model achieving SWE-bench (72.5%) and MMLU: 89.3% scores.\",\"model_version_group_id\":null,\"context_length\":1048576,\"input_modalities\":[\"text\",\"image\"],\"output_modalities\":[\"text\"],\"has_text_output\":true,\"group\":\"TestGroup\",\"instruct_type\":null,\"default_system\":null,\"default_stops\":[],\"hidden\":false,\"router\":null,\"warning_message\":\"Test warning\",\"promotion_message\":null,\"routing_error_message\":null,\"permaslug\":\"test/model-1-20260318\",\"supports_reasoning\":true,\"reasoning_config\":{\"start_token\":\"<think>\",\"end_token\":\"</think>\",\"reasoning_return_mechanism\":\"reasoning-content\"},\"features\":{\"reasoning_config\":{\"start_token\":\"<think>\",\"end_token\":\"</think>\",\"reasoning_return_mechanism\":\"reasoning-content\"},\"chat_template_config\":{}},\"default_parameters\":{\"temperature\":1,\"top_p\":0.95,\"top_k\":null,\"frequency_penalty\":null,\"presence_penalty\":null,\"repetition_penalty\":null},\"default_order\":[],\"quick_start_example_type\":\"reasoning\",\"is_trainable_text\":null,\"is_trainable_image\":null,\"knowledge_cutoff\":\"2025-01-31T23:59:59+00:00\",\"endpoint\":{\"id\":\"abc-123\",\"name\":\"TestProvider | test/model-1-20260318\",\"context_length\":1048576,\"model_variant_slug\":\"test/model-1\",\"model_variant_permaslug\":\"test/model-1-20260318\",\"adapter_name\":\"TestAdapter\",\"provider_name\":\"TestProvider\",\"provider_info\":{\"name\":\"TestProvider\",\"displayName\":\"TestProvider\",\"slug\":\"testprovider\",\"baseUrl\":\"https://api.test.com/v1\",\"dataPolicy\":{\"training\":false,\"trainingOpenRouter\":false,\"retainsPrompts\":true,\"retentionDays\":30,\"canPublish\":false,\"termsOfServiceURL\":\"https://test.com/terms\",\"privacyPolicyURL\":\"https://test.com/privacy\",\"requiresUserIDs\":true},\"headquarters\":\"US\",\"datacenters\":[\"US\",\"EU\"],\"regionOverrides\":{},\"hasChatCompletions\":true,\"hasCompletions\":false,\"isAbortable\":false,\"moderationRequired\":false,\"editors\":[],\"owners\":[],\"adapterName\":\"TestAdapter\",\"statusPageUrl\":\"https://status.test.com\",\"byokEnabled\":true,\"icon\":{\"url\":\"https://test.com/icon.png\"},\"ignoredProviderModels\":[],\"sendClientIp\":false,\"pricingStrategy\":\"test\"},\"provider_display_name\":\"TestProvider\",\"provider_slug\":\"testprovider/fp8\",\"provider_model_id\":\"test/model-1\",\"quantization\":\"fp8\",\"variant\":\"standard\",\"is_free\":false,\"can_abort\":false,\"max_prompt_tokens\":null,\"max_completion_tokens\":131072,\"max_tokens_per_image\":null,\"supported_parameters\":[\"reasoning\",\"max_tokens\",\"temperature\",\"tools\"],\"is_byok\":false,\"moderation_required\":false,\"data_policy\":{\"training\":false,\"trainingOpenRouter\":false,\"retainsPrompts\":true,\"retentionDays\":30,\"canPublish\":false,\"termsOfServiceURL\":\"https://test.com/terms\",\"privacyPolicyURL\":\"https://test.com/privacy\",\"requiresUserIDs\":true},\"pricing\":{\"prompt\":\"0.000001\",\"completion\":\"0.000003\",\"input_cache_read\":\"0.0000002\",\"discount\":0,\"line_items\":[{\"type\":\"long_context_threshold\",\"value\":\"256000\"},{\"type\":\"input_tokens_above_threshold\",\"value\":\"0.000002\"},{\"type\":\"output_tokens_above_threshold\",\"value\":\"0.000006\"},{\"type\":\"input_cache_read_tokens_above_threshold\",\"value\":\"0.0000004\"}]},\"variable_pricings\":[{\"type\":\"prompt-threshold\",\"threshold\":256000,\"prompt\":\"0.000002\",\"completions\":\"0.000006\",\"input_cache_read\":\"0.0000004\"}],\"line_items\":[{\"type\":\"long_context_threshold\",\"value\":\"256000\"},{\"type\":\"input_tokens_above_threshold\",\"value\":\"0.000002\"},{\"type\":\"output_tokens_above_threshold\",\"value\":\"0.000006\"},{\"type\":\"input_cache_read_tokens_above_threshold\",\"value\":\"0.0000004\"}],\"pricing_json\":{},\"pricing_version_id\":\"ver-1\",\"is_hidden\":false,\"is_deranked\":false,\"is_disabled\":false,\"supports_tool_parameters\":true,\"supports_reasoning\":true,\"supports_multipart\":true,\"limit_rpm\":null,\"limit_rpd\":null,\"limit_rpm_cf\":null,\"has_completions\":false,\"has_chat_completions\":true,\"features\":{\"supports_tool_choice\":{\"literal_none\":false,\"literal_auto\":true,\"literal_required\":true,\"type_function\":false}},\"supported_video_parameters\":null,\"provider_region\":null,\"deprecation_date\":null}},\"analytics\":[{\"date\":\"2026-03-26 00:00:00\",\"model_permaslug\":\"test/model-1-20260318\",\"variant\":\"standard\",\"total_completion_tokens\":870654946,\"total_prompt_tokens\":196873314447,\"total_native_tokens_reasoning\":231862032,\"count\":2037879,\"num_media_prompt\":445,\"num_media_completion\":0,\"num_audio_prompt\":0,\"total_native_tokens_cached\":177544227776,\"total_tool_calls\":1555637,\"requests_with_tool_call_errors\":36289,\"variant_permaslug\":\"test/model-1-20260318\"}],\"routerAnalytics\":[],\"modelNameMap\":{},\"variantGroups\":[{\"variant\":\"standard\",\"endpoints\":[{\"id\":\"abc-123\",\"name\":\"TestProvider | test/model-1-20260318\",\"context_length\":1048576,\"provider_name\":\"TestProvider\",\"provider_slug\":\"testprovider/fp8\",\"quantization\":\"fp8\",\"variant\":\"standard\",\"max_completion_tokens\":131072,\"max_prompt_tokens\":null,\"pricing\":{\"prompt\":\"0.000001\",\"completion\":\"0.000003\",\"input_cache_read\":\"0.0000002\",\"discount\":0},\"supported_parameters\":[\"reasoning\",\"max_tokens\",\"temperature\",\"tools\"],\"is_free\":false,\"is_byok\":false,\"moderation_required\":false,\"supports_tool_parameters\":true,\"supports_reasoning\":true,\"supports_multipart\":true,\"provider_region\":null}]}]}]\n"])</script>
<script>self.__next_f.push([1,"3d:[\"$\",\"$L40\",null,{\"hidden\":false,\"className\":\"test\",\"children\":[\"$\",\"$L41\",null,{\"categories\":[{\"date\":\"2026-03-25\",\"model\":\"test/model-1-20260318\",\"category\":\"programming\",\"count\":37890,\"total_prompt_tokens\":3722017129,\"total_completion_tokens\":16407354,\"volume\":42.661911,\"rank\":1},{\"date\":\"2026-03-25\",\"model\":\"test/model-1-20260318\",\"category\":\"technology\",\"count\":9627,\"total_prompt_tokens\":518751670,\"total_completion_tokens\":3604866,\"volume\":7.702767,\"rank\":3}]}]}]\n"])</script>
</body></html>
'''


@pytest.fixture
def sample_rsc_html():
    return SAMPLE_RSC_HTML


@pytest.fixture
def sample_api_models_response():
    """Minimal /api/v1/models response for one model."""
    return {
        "data": [
            {
                "id": "test/model-1",
                "name": "Test: Model-1",
                "created": 1773863643,
                "description": "A test model achieving SWE-bench (72.5%) and MMLU: 89.3% scores.",
                "context_length": 1048576,
                "architecture": {
                    "modality": "text+image->text",
                    "input_modalities": ["text", "image"],
                    "output_modalities": ["text"],
                    "tokenizer": "Other",
                    "instruct_type": None,
                },
                "pricing": {
                    "prompt": "0.000001",
                    "completion": "0.000003",
                    "input_cache_read": "0.0000002",
                },
                "top_provider": {
                    "context_length": 1048576,
                    "max_completion_tokens": 131072,
                    "is_moderated": False,
                },
                "per_request_limits": None,
                "supported_parameters": [
                    "reasoning",
                    "max_tokens",
                    "temperature",
                    "tools",
                ],
                "default_parameters": {
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": None,
                    "frequency_penalty": None,
                    "presence_penalty": None,
                    "repetition_penalty": None,
                },
                "knowledge_cutoff": "2025-01-31T23:59:59+00:00",
                "expiration_date": None,
            }
        ]
    }
```

- [ ] **Step 2: Write failing tests for RSC extraction**

Create `tests/test_rsc.py`:

```python
from scraper.rsc import extract_rsc_model_data, extract_rsc_categories


def test_extract_rsc_model_data_returns_model_dict(sample_rsc_html):
    result = extract_rsc_model_data(sample_rsc_html)
    assert result is not None
    assert result["model"]["slug"] == "test/model-1"
    assert result["model"]["name"] == "Test: Model-1"
    assert result["model"]["context_length"] == 1048576


def test_extract_rsc_model_data_includes_endpoint(sample_rsc_html):
    result = extract_rsc_model_data(sample_rsc_html)
    endpoint = result["model"]["endpoint"]
    assert endpoint["id"] == "abc-123"
    assert endpoint["provider_name"] == "TestProvider"
    assert endpoint["quantization"] == "fp8"


def test_extract_rsc_model_data_includes_provider_info(sample_rsc_html):
    result = extract_rsc_model_data(sample_rsc_html)
    provider = result["model"]["endpoint"]["provider_info"]
    assert provider["headquarters"] == "US"
    assert provider["datacenters"] == ["US", "EU"]
    assert provider["dataPolicy"]["retentionDays"] == 30


def test_extract_rsc_model_data_includes_analytics(sample_rsc_html):
    result = extract_rsc_model_data(sample_rsc_html)
    analytics = result["analytics"]
    assert len(analytics) == 1
    assert analytics[0]["count"] == 2037879
    assert analytics[0]["total_completion_tokens"] == 870654946


def test_extract_rsc_model_data_includes_variant_groups(sample_rsc_html):
    result = extract_rsc_model_data(sample_rsc_html)
    groups = result["variantGroups"]
    assert len(groups) == 1
    assert groups[0]["variant"] == "standard"
    assert len(groups[0]["endpoints"]) == 1


def test_extract_rsc_categories(sample_rsc_html):
    result = extract_rsc_categories(sample_rsc_html)
    assert len(result) == 2
    assert result[0]["category"] == "programming"
    assert result[0]["rank"] == 1
    assert result[1]["category"] == "technology"


def test_extract_rsc_model_data_returns_none_for_no_data():
    result = extract_rsc_model_data("<html><body></body></html>")
    assert result is None


def test_extract_rsc_categories_returns_empty_for_no_data():
    result = extract_rsc_categories("<html><body></body></html>")
    assert result == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_rsc.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scraper.rsc'`

- [ ] **Step 4: Implement rsc.py**

Create `scraper/rsc.py`:

```python
"""Extract model data from Next.js RSC flight payload in OpenRouter HTML pages."""

import json
import re


def _iter_rsc_chunks(html: str) -> list[str]:
    """Extract all RSC flight data strings from __next_f.push() calls."""
    pattern = r'self\.__next_f\.push\(\[1,"(.*?)"\]\)'
    matches = re.findall(pattern, html, re.DOTALL)
    chunks = []
    for m in matches:
        try:
            chunks.append(m.encode().decode("unicode_escape"))
        except (UnicodeDecodeError, ValueError):
            continue
    return chunks


def _extract_json_object(text: str, start_marker: str) -> dict | None:
    """Find and parse a JSON object starting at the given marker in text."""
    idx = text.find(start_marker)
    if idx < 0:
        return None
    # Walk forward to find the matching closing brace
    depth = 0
    for i in range(idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[idx : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def extract_rsc_model_data(html: str) -> dict | None:
    """Extract the full model data object from an OpenRouter model page HTML.

    Returns dict with keys: model, analytics, routerAnalytics, modelNameMap, variantGroups.
    Returns None if no model data found.
    """
    chunks = _iter_rsc_chunks(html)
    for chunk in chunks:
        obj = _extract_json_object(chunk, '{"model":{"slug":')
        if obj is not None:
            return obj
    return None


def extract_rsc_categories(html: str) -> list[dict]:
    """Extract use-case category rankings from an OpenRouter model page HTML.

    Returns list of category dicts with keys: date, model, category, count,
    total_prompt_tokens, total_completion_tokens, volume, rank.
    """
    chunks = _iter_rsc_chunks(html)
    for chunk in chunks:
        # Categories are in a different RSC chunk with "categories":[...]
        marker = '"categories":['
        idx = chunk.find(marker)
        if idx < 0:
            continue
        # Find the array
        arr_start = idx + len('"categories":')
        depth = 0
        for i in range(arr_start, len(chunk)):
            if chunk[i] == "[":
                depth += 1
            elif chunk[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(chunk[arr_start : i + 1])
                    except json.JSONDecodeError:
                        return []
    return []
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_rsc.py -v`
Expected: all 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add scraper/rsc.py tests/conftest.py tests/test_rsc.py tests/__init__.py
git commit -m "feat: RSC payload extractor for model page data"
```

---

## Task 3: Benchmark Extractor

**Files:**
- Create: `tests/test_benchmarks.py`
- Create: `scraper/benchmarks.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_benchmarks.py`:

```python
from scraper.benchmarks import extract_benchmarks


def test_extract_parenthesized_percentage():
    desc = "Leading results on SWE-bench (72.5%) and Terminal-bench (43.2%)."
    results = extract_benchmarks(desc)
    assert {"benchmark_name": "SWE-bench", "score": 72.5, "unit": "%"} in results
    assert {"benchmark_name": "Terminal-bench", "score": 43.2, "unit": "%"} in results


def test_extract_colon_percentage():
    desc = "Scores include MMLU: 89.3% and HellaSwag: 95.1% on standard benchmarks."
    results = extract_benchmarks(desc)
    assert {"benchmark_name": "MMLU", "score": 89.3, "unit": "%"} in results
    assert {"benchmark_name": "HellaSwag", "score": 95.1, "unit": "%"} in results


def test_extract_mixed_formats():
    desc = "Achieves SWE-bench (72.5%) with MMLU: 89.3% performance."
    results = extract_benchmarks(desc)
    assert len(results) == 2


def test_no_benchmarks():
    desc = "A general-purpose language model with no benchmark data."
    results = extract_benchmarks(desc)
    assert results == []


def test_no_duplicates():
    desc = "SWE-bench (72.5%) is great. Also SWE-bench (72.5%) again."
    results = extract_benchmarks(desc)
    swe = [r for r in results if r["benchmark_name"] == "SWE-bench"]
    assert len(swe) == 1


def test_integer_score():
    desc = "Achieves HumanEval (92%) pass rate."
    results = extract_benchmarks(desc)
    assert {"benchmark_name": "HumanEval", "score": 92.0, "unit": "%"} in results
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_benchmarks.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement benchmarks.py**

Create `scraper/benchmarks.py`:

```python
"""Extract benchmark scores from model description text."""

import re


def extract_benchmarks(description: str) -> list[dict]:
    """Extract benchmark name/score pairs from free-text description.

    Supports formats:
    - "BenchName (72.5%)" — parenthesized percentage
    - "BenchName: 89.3%" — colon-separated percentage

    Returns list of dicts: {benchmark_name, score, unit}
    """
    results: dict[str, dict] = {}  # keyed by benchmark_name for dedup

    # Pattern 1: "Name (72.5%)"
    for m in re.finditer(r"([\w][\w\s-]*?)\s*\((\d+\.?\d*)%\)", description):
        name = m.group(1).strip()
        score = float(m.group(2))
        results[name] = {"benchmark_name": name, "score": score, "unit": "%"}

    # Pattern 2: "Name: 72.5%"
    for m in re.finditer(r"([\w][\w\s-]*?):\s*(\d+\.?\d*)%", description):
        name = m.group(1).strip()
        score = float(m.group(2))
        if name not in results:
            results[name] = {"benchmark_name": name, "score": score, "unit": "%"}

    return list(results.values())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_benchmarks.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/benchmarks.py tests/test_benchmarks.py
git commit -m "feat: benchmark score extractor from description text"
```

---

## Task 4: JSON-to-Row Transformer

**Files:**
- Create: `tests/test_transform.py`
- Create: `scraper/transform.py`

This transforms the nested RSC JSON into flat row dicts matching each table's schema.

- [ ] **Step 1: Write failing tests**

Create `tests/test_transform.py`:

```python
from scraper.transform import (
    transform_model,
    transform_endpoints,
    transform_provider,
    transform_analytics,
    transform_categories,
)


def _make_rsc_data():
    """Return the parsed RSC model data dict (same structure as extract_rsc_model_data output)."""
    return {
        "model": {
            "slug": "test/model-1",
            "hf_slug": "test-org/model-1",
            "name": "Test: Model-1",
            "short_name": "Model-1",
            "author": "test",
            "description": "A test model.",
            "context_length": 200000,
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "group": "TestGroup",
            "instruct_type": None,
            "supports_reasoning": True,
            "knowledge_cutoff": "2025-01-31T23:59:59+00:00",
            "permaslug": "test/model-1-20260318",
            "created_at": "2026-03-18T19:54:03.793004+00:00",
            "updated_at": "2026-03-25T15:39:42.591683+00:00",
            "warning_message": None,
            "default_parameters": {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": None,
                "frequency_penalty": None,
                "presence_penalty": None,
                "repetition_penalty": None,
            },
            "endpoint": {
                "id": "abc-123",
                "name": "TestProvider | test/model-1-20260318",
                "context_length": 200000,
                "provider_name": "TestProvider",
                "provider_slug": "testprovider/fp8",
                "quantization": "fp8",
                "variant": "standard",
                "max_completion_tokens": 32000,
                "max_prompt_tokens": None,
                "is_free": False,
                "is_byok": False,
                "moderation_required": False,
                "supports_tool_parameters": True,
                "supports_reasoning": True,
                "supports_multipart": True,
                "provider_region": None,
                "supported_parameters": ["reasoning", "max_tokens", "tools"],
                "pricing": {
                    "prompt": "0.000015",
                    "completion": "0.000075",
                    "input_cache_read": "0.0000015",
                    "input_cache_write": "0.00001875",
                    "discount": 0,
                    "line_items": [
                        {"type": "long_context_threshold", "value": "128000"},
                        {"type": "input_tokens_above_threshold", "value": "0.00003"},
                        {"type": "output_tokens_above_threshold", "value": "0.00015"},
                    ],
                },
                "variable_pricings": [
                    {
                        "type": "prompt-threshold",
                        "threshold": 128000,
                        "prompt": "0.00003",
                        "completions": "0.00015",
                    }
                ],
                "provider_info": {
                    "name": "TestProvider",
                    "displayName": "TestProvider",
                    "slug": "testprovider",
                    "baseUrl": "https://api.test.com/v1",
                    "dataPolicy": {
                        "training": False,
                        "trainingOpenRouter": False,
                        "retainsPrompts": True,
                        "retentionDays": 30,
                        "canPublish": False,
                        "termsOfServiceURL": "https://test.com/terms",
                        "privacyPolicyURL": "https://test.com/privacy",
                        "requiresUserIDs": True,
                    },
                    "headquarters": "US",
                    "datacenters": ["US", "EU"],
                    "isAbortable": False,
                    "moderationRequired": False,
                    "adapterName": "TestAdapter",
                    "statusPageUrl": "https://status.test.com",
                    "byokEnabled": True,
                },
            },
        },
        "analytics": [
            {
                "date": "2026-03-26 00:00:00",
                "model_permaslug": "test/model-1-20260318",
                "variant": "standard",
                "total_completion_tokens": 870654946,
                "total_prompt_tokens": 196873314447,
                "total_native_tokens_reasoning": 231862032,
                "count": 2037879,
                "num_media_prompt": 445,
                "num_media_completion": 0,
                "num_audio_prompt": 0,
                "total_native_tokens_cached": 177544227776,
                "total_tool_calls": 1555637,
                "requests_with_tool_call_errors": 36289,
            }
        ],
        "variantGroups": [
            {
                "variant": "standard",
                "endpoints": [
                    {
                        "id": "abc-123",
                        "name": "TestProvider | test/model-1-20260318",
                        "context_length": 200000,
                        "provider_name": "TestProvider",
                        "provider_slug": "testprovider/fp8",
                        "quantization": "fp8",
                        "variant": "standard",
                        "max_completion_tokens": 32000,
                        "max_prompt_tokens": None,
                        "pricing": {
                            "prompt": "0.000015",
                            "completion": "0.000075",
                            "input_cache_read": "0.0000015",
                            "discount": 0,
                        },
                        "supported_parameters": ["reasoning", "max_tokens", "tools"],
                        "is_free": False,
                        "is_byok": False,
                        "moderation_required": False,
                        "supports_tool_parameters": True,
                        "supports_reasoning": True,
                        "supports_multipart": True,
                        "provider_region": None,
                    }
                ],
            }
        ],
    }


def test_transform_model():
    data = _make_rsc_data()
    row = transform_model(data)
    assert row["slug"] == "test/model-1"
    assert row["name"] == "Test: Model-1"
    assert row["short_name"] == "Model-1"
    assert row["author"] == "test"
    assert row["context_length"] == 200000
    assert row["input_modalities"] == ["text", "image"]
    assert row["supports_reasoning"] is True
    assert row["default_temperature"] == 1
    assert row["default_top_p"] == 0.95
    assert row["default_top_k"] is None
    assert row["group"] == "TestGroup"
    assert "scraped_at" in row


def test_transform_endpoints():
    data = _make_rsc_data()
    rows = transform_endpoints(data)
    assert len(rows) == 1
    ep = rows[0]
    assert ep["endpoint_id"] == "abc-123"
    assert ep["model_slug"] == "test/model-1"
    assert ep["provider_slug"] == "testprovider"
    assert ep["quantization"] == "fp8"
    assert ep["pricing_prompt"] == "0.000015"
    assert ep["pricing_completion"] == "0.000075"
    assert ep["long_ctx_threshold"] == 128000
    assert ep["long_ctx_prompt_price"] == "0.00003"
    assert ep["long_ctx_completion_price"] == "0.00015"
    assert ep["supported_parameters"] == ["reasoning", "max_tokens", "tools"]


def test_transform_provider():
    data = _make_rsc_data()
    row = transform_provider(data)
    assert row["slug"] == "testprovider"
    assert row["name"] == "TestProvider"
    assert row["headquarters"] == "US"
    assert row["datacenters"] == ["US", "EU"]
    assert row["training"] is False
    assert row["retention_days"] == 30
    assert row["terms_url"] == "https://test.com/terms"
    assert row["byok_enabled"] is True
    assert row["adapter_name"] == "TestAdapter"


def test_transform_analytics():
    data = _make_rsc_data()
    rows = transform_analytics(data)
    assert len(rows) == 1
    a = rows[0]
    assert a["model_slug"] == "test/model-1"
    assert a["date"] == "2026-03-26"
    assert a["request_count"] == 2037879
    assert a["completion_tokens"] == 870654946
    assert a["reasoning_tokens"] == 231862032
    assert a["cached_tokens"] == 177544227776
    assert a["tool_calls"] == 1555637


def test_transform_categories():
    categories_raw = [
        {
            "date": "2026-03-25",
            "model": "test/model-1-20260318",
            "category": "programming",
            "count": 37890,
            "total_prompt_tokens": 3722017129,
            "total_completion_tokens": 16407354,
            "volume": 42.661911,
            "rank": 1,
        }
    ]
    rows = transform_categories("test/model-1", categories_raw)
    assert len(rows) == 1
    c = rows[0]
    assert c["model_slug"] == "test/model-1"
    assert c["category"] == "programming"
    assert c["rank"] == 1
    assert c["volume"] == 42.661911
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_transform.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement transform.py**

Create `scraper/transform.py`:

```python
"""Transform nested RSC JSON into flat row dicts for each Parquet table."""

from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def transform_model(rsc_data: dict) -> dict:
    """Transform RSC model data into a flat row for the models table."""
    m = rsc_data["model"]
    defaults = m.get("default_parameters") or {}
    arch = m.get("architecture") or {}
    return {
        "slug": m["slug"],
        "name": m["name"],
        "short_name": m.get("short_name"),
        "author": m.get("author"),
        "description": m.get("description"),
        "context_length": m.get("context_length"),
        "group": m.get("group"),
        "input_modalities": m.get("input_modalities", []),
        "output_modalities": m.get("output_modalities", []),
        "supports_reasoning": m.get("supports_reasoning", False),
        "knowledge_cutoff": m.get("knowledge_cutoff"),
        "permaslug": m.get("permaslug"),
        "hf_slug": m.get("hf_slug"),
        "created_at": m.get("created_at"),
        "updated_at": m.get("updated_at"),
        "warning_message": m.get("warning_message"),
        "default_temperature": defaults.get("temperature"),
        "default_top_p": defaults.get("top_p"),
        "default_top_k": defaults.get("top_k"),
        "default_frequency_penalty": defaults.get("frequency_penalty"),
        "default_presence_penalty": defaults.get("presence_penalty"),
        "default_repetition_penalty": defaults.get("repetition_penalty"),
        "instruct_type": m.get("instruct_type") or arch.get("instruct_type"),
        "tokenizer": arch.get("tokenizer"),
        "scraped_at": _now_iso(),
    }


def _parse_long_ctx(endpoint: dict) -> dict:
    """Extract long-context pricing from line_items or variable_pricings."""
    result = {
        "long_ctx_threshold": None,
        "long_ctx_prompt_price": None,
        "long_ctx_completion_price": None,
        "long_ctx_cache_read_price": None,
    }

    # Try variable_pricings first (most structured)
    for vp in endpoint.get("variable_pricings") or []:
        if vp.get("type") == "prompt-threshold":
            result["long_ctx_threshold"] = vp.get("threshold")
            result["long_ctx_prompt_price"] = vp.get("prompt")
            result["long_ctx_completion_price"] = vp.get("completions")
            result["long_ctx_cache_read_price"] = vp.get("input_cache_read")
            return result

    # Fallback to line_items
    for item in endpoint.get("line_items") or []:
        t = item.get("type", "")
        v = item.get("value")
        if t == "long_context_threshold":
            result["long_ctx_threshold"] = int(v) if v else None
        elif t == "input_tokens_above_threshold":
            result["long_ctx_prompt_price"] = v
        elif t == "output_tokens_above_threshold":
            result["long_ctx_completion_price"] = v
        elif t == "input_cache_read_tokens_above_threshold":
            result["long_ctx_cache_read_price"] = v

    return result


def transform_endpoints(rsc_data: dict) -> list[dict]:
    """Transform RSC data into flat rows for the model_endpoints table.

    Uses variantGroups for multi-provider models, falls back to single endpoint.
    """
    model_slug = rsc_data["model"]["slug"]
    main_endpoint = rsc_data["model"].get("endpoint", {})
    rows = []

    # Collect all endpoints from variantGroups
    all_endpoints = []
    for group in rsc_data.get("variantGroups") or []:
        for ep in group.get("endpoints") or []:
            all_endpoints.append((group.get("variant", "standard"), ep))

    # If no variantGroups, use the main endpoint
    if not all_endpoints and main_endpoint:
        all_endpoints.append((main_endpoint.get("variant", "standard"), main_endpoint))

    for variant, ep in all_endpoints:
        pricing = ep.get("pricing") or {}
        # Provider slug: strip quantization suffix (e.g., "testprovider/fp8" -> "testprovider")
        raw_provider_slug = ep.get("provider_slug", "")
        provider_slug = raw_provider_slug.split("/")[0] if "/" in raw_provider_slug else raw_provider_slug

        # For long-context pricing, check the main endpoint which has full data
        long_ctx_source = main_endpoint if main_endpoint.get("id") == ep.get("id") else ep
        long_ctx = _parse_long_ctx(long_ctx_source)

        rows.append({
            "endpoint_id": ep.get("id"),
            "model_slug": model_slug,
            "provider_slug": provider_slug,
            "endpoint_name": ep.get("name"),
            "quantization": ep.get("quantization"),
            "variant": variant,
            "context_length": ep.get("context_length"),
            "max_completion_tokens": ep.get("max_completion_tokens"),
            "max_prompt_tokens": ep.get("max_prompt_tokens"),
            "pricing_prompt": pricing.get("prompt"),
            "pricing_completion": pricing.get("completion"),
            "pricing_cache_read": pricing.get("input_cache_read"),
            "pricing_cache_write": pricing.get("input_cache_write"),
            "pricing_image": pricing.get("image"),
            "pricing_web_search": pricing.get("web_search"),
            "pricing_discount": pricing.get("discount", 0),
            **long_ctx,
            "uptime_30m": ep.get("uptime_last_30m"),
            "latency_30m": ep.get("latency_last_30m"),
            "throughput_30m": ep.get("throughput_last_30m"),
            "is_moderated": ep.get("moderation_required", False),
            "is_byok": ep.get("is_byok", False),
            "is_free": ep.get("is_free", False),
            "supported_parameters": ep.get("supported_parameters", []),
            "supports_tool_parameters": ep.get("supports_tool_parameters", False),
            "supports_reasoning": ep.get("supports_reasoning", False),
            "supports_multipart": ep.get("supports_multipart", False),
            "provider_region": ep.get("provider_region"),
            "scraped_at": _now_iso(),
        })

    return rows


def transform_provider(rsc_data: dict) -> dict | None:
    """Transform RSC data into a flat row for the providers table."""
    endpoint = rsc_data["model"].get("endpoint")
    if not endpoint:
        return None
    info = endpoint.get("provider_info")
    if not info:
        return None
    policy = info.get("dataPolicy") or {}
    return {
        "slug": info.get("slug"),
        "name": info.get("name"),
        "base_url": info.get("baseUrl"),
        "headquarters": info.get("headquarters"),
        "datacenters": info.get("datacenters", []),
        "training": policy.get("training", False),
        "training_openrouter": policy.get("trainingOpenRouter", False),
        "retains_prompts": policy.get("retainsPrompts", False),
        "retention_days": policy.get("retentionDays"),
        "can_publish": policy.get("canPublish", False),
        "requires_user_ids": policy.get("requiresUserIDs", False),
        "terms_url": policy.get("termsOfServiceURL"),
        "privacy_url": policy.get("privacyPolicyURL"),
        "byok_enabled": info.get("byokEnabled", False),
        "is_abortable": info.get("isAbortable", False),
        "moderation_required": info.get("moderationRequired", False),
        "adapter_name": info.get("adapterName"),
        "status_page_url": info.get("statusPageUrl"),
        "scraped_at": _now_iso(),
    }


def transform_analytics(rsc_data: dict) -> list[dict]:
    """Transform RSC analytics array into flat rows for the model_analytics table."""
    model_slug = rsc_data["model"]["slug"]
    rows = []
    for a in rsc_data.get("analytics") or []:
        date_str = a.get("date", "")[:10]  # "2026-03-26 00:00:00" -> "2026-03-26"
        rows.append({
            "model_slug": model_slug,
            "date": date_str,
            "request_count": a.get("count", 0),
            "completion_tokens": a.get("total_completion_tokens", 0),
            "prompt_tokens": a.get("total_prompt_tokens", 0),
            "reasoning_tokens": a.get("total_native_tokens_reasoning", 0),
            "cached_tokens": a.get("total_native_tokens_cached", 0),
            "tool_calls": a.get("total_tool_calls", 0),
            "tool_call_errors": a.get("requests_with_tool_call_errors", 0),
            "media_prompt_count": a.get("num_media_prompt", 0),
            "media_completion_count": a.get("num_media_completion", 0),
            "audio_prompt_count": a.get("num_audio_prompt", 0),
        })
    return rows


def transform_categories(model_slug: str, categories: list[dict]) -> list[dict]:
    """Transform RSC category rankings into flat rows for the model_categories table."""
    rows = []
    for c in categories:
        rows.append({
            "model_slug": model_slug,
            "date": c.get("date", "")[:10],
            "category": c.get("category"),
            "rank": c.get("rank"),
            "volume": c.get("volume"),
            "request_count": c.get("count", 0),
            "prompt_tokens": c.get("total_prompt_tokens", 0),
            "completion_tokens": c.get("total_completion_tokens", 0),
        })
    return rows
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_transform.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/transform.py tests/test_transform.py
git commit -m "feat: JSON-to-row transformer for all six tables"
```

---

## Task 5: Parquet Writer

**Files:**
- Create: `tests/test_parquet.py`
- Create: `scraper/parquet.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_parquet.py`:

```python
import pyarrow.parquet as pq
from pathlib import Path
from scraper.parquet import write_models, write_endpoints, write_providers, write_benchmarks, write_analytics, write_categories


def test_write_models_roundtrip(tmp_path):
    rows = [
        {
            "slug": "test/model-1",
            "name": "Test Model",
            "short_name": "Model",
            "author": "test",
            "description": "desc",
            "context_length": 200000,
            "group": "TestGroup",
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "supports_reasoning": True,
            "knowledge_cutoff": "2025-01-31T23:59:59+00:00",
            "permaslug": "test/model-1-20260318",
            "hf_slug": "",
            "created_at": "2026-03-18T19:54:03+00:00",
            "updated_at": "2026-03-25T15:39:42+00:00",
            "warning_message": None,
            "default_temperature": 1.0,
            "default_top_p": 0.95,
            "default_top_k": None,
            "default_frequency_penalty": None,
            "default_presence_penalty": None,
            "default_repetition_penalty": None,
            "instruct_type": None,
            "tokenizer": "Other",
            "scraped_at": "2026-03-26T12:00:00+00:00",
        }
    ]
    out = tmp_path / "models.parquet"
    write_models(rows, str(out))
    table = pq.read_table(str(out))
    assert table.num_rows == 1
    assert table.column("slug").to_pylist() == ["test/model-1"]
    assert table.column("input_modalities").to_pylist() == [["text", "image"]]
    assert table.column("context_length").to_pylist() == [200000]


def test_write_endpoints_roundtrip(tmp_path):
    rows = [
        {
            "endpoint_id": "abc-123",
            "model_slug": "test/model-1",
            "provider_slug": "testprovider",
            "endpoint_name": "TestProvider | test/model-1",
            "quantization": "fp8",
            "variant": "standard",
            "context_length": 200000,
            "max_completion_tokens": 32000,
            "max_prompt_tokens": None,
            "pricing_prompt": "0.000015",
            "pricing_completion": "0.000075",
            "pricing_cache_read": "0.0000015",
            "pricing_cache_write": "0.00001875",
            "pricing_image": None,
            "pricing_web_search": None,
            "pricing_discount": 0.0,
            "long_ctx_threshold": 128000,
            "long_ctx_prompt_price": "0.00003",
            "long_ctx_completion_price": "0.00015",
            "long_ctx_cache_read_price": None,
            "uptime_30m": 100.0,
            "latency_30m": None,
            "throughput_30m": None,
            "is_moderated": False,
            "is_byok": False,
            "is_free": False,
            "supported_parameters": ["reasoning", "max_tokens", "tools"],
            "supports_tool_parameters": True,
            "supports_reasoning": True,
            "supports_multipart": True,
            "provider_region": None,
            "scraped_at": "2026-03-26T12:00:00+00:00",
        }
    ]
    out = tmp_path / "endpoints.parquet"
    write_endpoints(rows, str(out))
    table = pq.read_table(str(out))
    assert table.num_rows == 1
    assert table.column("endpoint_id").to_pylist() == ["abc-123"]
    assert table.column("supported_parameters").to_pylist() == [
        ["reasoning", "max_tokens", "tools"]
    ]


def test_write_benchmarks_roundtrip(tmp_path):
    rows = [
        {
            "model_slug": "test/model-1",
            "benchmark_name": "SWE-bench",
            "score": 72.5,
            "unit": "%",
            "source": "description",
        }
    ]
    out = tmp_path / "benchmarks.parquet"
    write_benchmarks(rows, str(out))
    table = pq.read_table(str(out))
    assert table.num_rows == 1
    assert table.column("score").to_pylist() == [72.5]


def test_write_empty_table(tmp_path):
    out = tmp_path / "empty.parquet"
    write_models([], str(out))
    table = pq.read_table(str(out))
    assert table.num_rows == 0
    assert "slug" in table.column_names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_parquet.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement parquet.py**

Create `scraper/parquet.py`:

```python
"""Define PyArrow schemas and write row dicts to Parquet files."""

import pyarrow as pa
import pyarrow.parquet as pq


MODELS_SCHEMA = pa.schema([
    ("slug", pa.string()),
    ("name", pa.string()),
    ("short_name", pa.string()),
    ("author", pa.string()),
    ("description", pa.string()),
    ("context_length", pa.int64()),
    ("group", pa.string()),
    ("input_modalities", pa.list_(pa.string())),
    ("output_modalities", pa.list_(pa.string())),
    ("supports_reasoning", pa.bool_()),
    ("knowledge_cutoff", pa.string()),
    ("permaslug", pa.string()),
    ("hf_slug", pa.string()),
    ("created_at", pa.string()),
    ("updated_at", pa.string()),
    ("warning_message", pa.string()),
    ("default_temperature", pa.float64()),
    ("default_top_p", pa.float64()),
    ("default_top_k", pa.int64()),
    ("default_frequency_penalty", pa.float64()),
    ("default_presence_penalty", pa.float64()),
    ("default_repetition_penalty", pa.float64()),
    ("instruct_type", pa.string()),
    ("tokenizer", pa.string()),
    ("scraped_at", pa.string()),
])

ENDPOINTS_SCHEMA = pa.schema([
    ("endpoint_id", pa.string()),
    ("model_slug", pa.string()),
    ("provider_slug", pa.string()),
    ("endpoint_name", pa.string()),
    ("quantization", pa.string()),
    ("variant", pa.string()),
    ("context_length", pa.int64()),
    ("max_completion_tokens", pa.int64()),
    ("max_prompt_tokens", pa.int64()),
    ("pricing_prompt", pa.string()),
    ("pricing_completion", pa.string()),
    ("pricing_cache_read", pa.string()),
    ("pricing_cache_write", pa.string()),
    ("pricing_image", pa.string()),
    ("pricing_web_search", pa.string()),
    ("pricing_discount", pa.float64()),
    ("long_ctx_threshold", pa.int64()),
    ("long_ctx_prompt_price", pa.string()),
    ("long_ctx_completion_price", pa.string()),
    ("long_ctx_cache_read_price", pa.string()),
    ("uptime_30m", pa.float64()),
    ("latency_30m", pa.float64()),
    ("throughput_30m", pa.float64()),
    ("is_moderated", pa.bool_()),
    ("is_byok", pa.bool_()),
    ("is_free", pa.bool_()),
    ("supported_parameters", pa.list_(pa.string())),
    ("supports_tool_parameters", pa.bool_()),
    ("supports_reasoning", pa.bool_()),
    ("supports_multipart", pa.bool_()),
    ("provider_region", pa.string()),
    ("scraped_at", pa.string()),
])

PROVIDERS_SCHEMA = pa.schema([
    ("slug", pa.string()),
    ("name", pa.string()),
    ("base_url", pa.string()),
    ("headquarters", pa.string()),
    ("datacenters", pa.list_(pa.string())),
    ("training", pa.bool_()),
    ("training_openrouter", pa.bool_()),
    ("retains_prompts", pa.bool_()),
    ("retention_days", pa.int64()),
    ("can_publish", pa.bool_()),
    ("requires_user_ids", pa.bool_()),
    ("terms_url", pa.string()),
    ("privacy_url", pa.string()),
    ("byok_enabled", pa.bool_()),
    ("is_abortable", pa.bool_()),
    ("moderation_required", pa.bool_()),
    ("adapter_name", pa.string()),
    ("status_page_url", pa.string()),
    ("scraped_at", pa.string()),
])

BENCHMARKS_SCHEMA = pa.schema([
    ("model_slug", pa.string()),
    ("benchmark_name", pa.string()),
    ("score", pa.float64()),
    ("unit", pa.string()),
    ("source", pa.string()),
])

ANALYTICS_SCHEMA = pa.schema([
    ("model_slug", pa.string()),
    ("date", pa.string()),
    ("request_count", pa.int64()),
    ("completion_tokens", pa.int64()),
    ("prompt_tokens", pa.int64()),
    ("reasoning_tokens", pa.int64()),
    ("cached_tokens", pa.int64()),
    ("tool_calls", pa.int64()),
    ("tool_call_errors", pa.int64()),
    ("media_prompt_count", pa.int64()),
    ("media_completion_count", pa.int64()),
    ("audio_prompt_count", pa.int64()),
])

CATEGORIES_SCHEMA = pa.schema([
    ("model_slug", pa.string()),
    ("date", pa.string()),
    ("category", pa.string()),
    ("rank", pa.int64()),
    ("volume", pa.float64()),
    ("request_count", pa.int64()),
    ("prompt_tokens", pa.int64()),
    ("completion_tokens", pa.int64()),
])


def _write(rows: list[dict], schema: pa.Schema, path: str) -> None:
    """Write a list of row dicts to a Parquet file with the given schema."""
    if not rows:
        # Write empty table with correct schema
        table = pa.table({f.name: pa.array([], type=f.type) for f in schema}, schema=schema)
    else:
        arrays = {}
        for field in schema:
            values = [row.get(field.name) for row in rows]
            arrays[field.name] = pa.array(values, type=field.type)
        table = pa.table(arrays, schema=schema)
    pq.write_table(table, path)


def write_models(rows: list[dict], path: str) -> None:
    _write(rows, MODELS_SCHEMA, path)


def write_endpoints(rows: list[dict], path: str) -> None:
    _write(rows, ENDPOINTS_SCHEMA, path)


def write_providers(rows: list[dict], path: str) -> None:
    _write(rows, PROVIDERS_SCHEMA, path)


def write_benchmarks(rows: list[dict], path: str) -> None:
    _write(rows, BENCHMARKS_SCHEMA, path)


def write_analytics(rows: list[dict], path: str) -> None:
    _write(rows, ANALYTICS_SCHEMA, path)


def write_categories(rows: list[dict], path: str) -> None:
    _write(rows, CATEGORIES_SCHEMA, path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_parquet.py -v`
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/parquet.py tests/test_parquet.py
git commit -m "feat: Parquet writer with schemas for all six tables"
```

---

## Task 6: API Client

**Files:**
- Create: `scraper/api.py`

No separate test file — this is a thin HTTP wrapper. It will be integration-tested when we run the full pipeline.

- [ ] **Step 1: Implement api.py**

Create `scraper/api.py`:

```python
"""Fetch model data from OpenRouter public API and model pages."""

import asyncio
import httpx

BASE_URL = "https://openrouter.ai"
CONCURRENCY_LIMIT = 10
REQUEST_DELAY = 0.1  # seconds between batches


async def fetch_model_list(client: httpx.AsyncClient) -> list[dict]:
    """Fetch all models from /api/v1/models. Returns the 'data' array."""
    resp = await client.get(f"{BASE_URL}/api/v1/models")
    resp.raise_for_status()
    return resp.json()["data"]


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
```

- [ ] **Step 2: Commit**

```bash
git add scraper/api.py
git commit -m "feat: async API client for model list and page fetching"
```

---

## Task 7: Main Orchestrator

**Files:**
- Create: `scraper/main.py`

- [ ] **Step 1: Implement main.py**

Create `scraper/main.py`:

```python
"""Main orchestrator: fetch all models → transform → write Parquet files."""

import asyncio
import sys
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
from scraper.parquet import (
    write_models,
    write_endpoints,
    write_providers,
    write_benchmarks,
    write_analytics,
    write_categories,
)

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

    # Accumulators for all tables
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
        # Supplement with API data (tokenizer, instruct_type come from API)
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

    print("4. Writing Parquet files...")
    write_models(all_models, str(output_dir / "models.parquet"))
    write_endpoints(all_endpoints, str(output_dir / "model_endpoints.parquet"))
    write_providers(list(all_providers.values()), str(output_dir / "providers.parquet"))
    write_benchmarks(all_benchmarks, str(output_dir / "model_benchmarks.parquet"))
    write_analytics(all_analytics, str(output_dir / "model_analytics.parquet"))
    write_categories(all_categories, str(output_dir / "model_categories.parquet"))
    print(f"   Written to {output_dir}/")


def cli():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape OpenRouter model data to Parquet")
    parser.add_argument("-o", "--output", default=str(DATA_DIR), help="Output directory")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Max concurrent requests")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="Delay between requests (seconds)")
    args = parser.parse_args()

    asyncio.run(scrape(
        output_dir=Path(args.output),
        concurrency=args.concurrency,
        delay=args.delay,
    ))


if __name__ == "__main__":
    cli()
```

- [ ] **Step 2: Commit**

```bash
git add scraper/main.py
git commit -m "feat: main orchestrator for full scrape pipeline"
```

---

## Task 8: Example Queries

**Files:**
- Create: `queries/examples.sql`

- [ ] **Step 1: Write example queries**

Create `queries/examples.sql`:

```sql
-- ============================================================
-- Example DuckDB queries for the OpenRouter model database
-- Usage: duckdb < queries/examples.sql
--   or:  duckdb -c "SELECT ... FROM 'data/models.parquet' ..."
-- ============================================================

-- All reasoning models sorted by price
SELECT m.name, m.context_length,
       e.pricing_prompt, e.pricing_completion,
       e.provider_slug, e.latency_30m, e.throughput_30m
FROM 'data/models.parquet' m
JOIN 'data/model_endpoints.parquet' e ON m.slug = e.model_slug
WHERE m.supports_reasoning = true
ORDER BY CAST(e.pricing_prompt AS DOUBLE) ASC;

-- Cheapest models with >100k context
SELECT m.name, m.context_length,
       CAST(e.pricing_prompt AS DOUBLE) * 1000000 AS price_per_m_input,
       CAST(e.pricing_completion AS DOUBLE) * 1000000 AS price_per_m_output
FROM 'data/models.parquet' m
JOIN 'data/model_endpoints.parquet' e ON m.slug = e.model_slug
WHERE m.context_length > 100000
ORDER BY price_per_m_input ASC
LIMIT 20;

-- Benchmark leaderboard
SELECT m.name, b.benchmark_name, b.score
FROM 'data/model_benchmarks.parquet' b
JOIN 'data/models.parquet' m ON m.slug = b.model_slug
ORDER BY b.benchmark_name, b.score DESC;

-- Provider data policy comparison
SELECT name, headquarters, training, retains_prompts,
       retention_days, requires_user_ids, byok_enabled
FROM 'data/providers.parquet'
ORDER BY name;

-- Most popular models by request volume (latest day)
SELECT a.model_slug, m.name, a.request_count,
       a.completion_tokens, a.tool_calls
FROM 'data/model_analytics.parquet' a
JOIN 'data/models.parquet' m ON m.slug = a.model_slug
WHERE a.date = (SELECT MAX(date) FROM 'data/model_analytics.parquet')
ORDER BY a.request_count DESC
LIMIT 20;

-- Top programming models by category rank
SELECT c.model_slug, m.name, c.rank, c.volume
FROM 'data/model_categories.parquet' c
JOIN 'data/models.parquet' m ON m.slug = c.model_slug
WHERE c.category = 'programming'
  AND c.date = (SELECT MAX(date) FROM 'data/model_categories.parquet')
ORDER BY c.rank ASC;

-- Models that support tool calling
SELECT m.name, e.provider_slug, e.pricing_prompt
FROM 'data/models.parquet' m
JOIN 'data/model_endpoints.parquet' e ON m.slug = e.model_slug
WHERE list_contains(e.supported_parameters, 'tools')
ORDER BY m.name;

-- Free models
SELECT m.name, e.provider_slug, m.context_length
FROM 'data/models.parquet' m
JOIN 'data/model_endpoints.parquet' e ON m.slug = e.model_slug
WHERE e.is_free = true
ORDER BY m.context_length DESC;
```

- [ ] **Step 2: Commit**

```bash
git add queries/examples.sql
git commit -m "docs: example DuckDB queries for model database"
```

---

## Task 9: Integration Test — Run Full Pipeline

- [ ] **Step 1: Run the full scraper**

Run: `python -m scraper.main -o data/ -c 10 -d 0.1`

Expected output (approximate):
```
1. Fetching model list from API...
   Found ~400+ models
2. Fetching model pages...
   [400/400] ...
   Fetched ~400 pages
3. Transforming data...
   Processed ~400 models, skipped ~0-5
   ~600+ endpoints, ~30+ providers
   ~50+ benchmarks, ~3000+ analytics rows
   ~1000+ category rows
4. Writing Parquet files...
   Written to data/
```

- [ ] **Step 2: Verify Parquet files are readable**

Run: `python -c "import pyarrow.parquet as pq; t = pq.read_table('data/models.parquet'); print(f'{t.num_rows} models, columns: {t.column_names}')"`

Expected: `~400+ models, columns: ['slug', 'name', ...]`

- [ ] **Step 3: Verify with DuckDB (if installed)**

Run: `duckdb -c "SELECT name, context_length FROM 'data/models.parquet' ORDER BY context_length DESC LIMIT 5;"`

Expected: top 5 models by context length

- [ ] **Step 4: Fix any issues found during integration**

If the scraper fails or produces unexpected data, debug and fix. Common issues:
- Rate limiting (increase delay)
- Missing fields on some models (add null handling)
- RSC payload format changes (update extraction regex)

- [ ] **Step 5: Commit data directory to .gitignore**

Create `.gitignore`:
```
data/*.parquet
__pycache__/
*.egg-info/
.venv/
```

```bash
git add .gitignore
git commit -m "chore: add .gitignore for parquet data and Python artifacts"
```
