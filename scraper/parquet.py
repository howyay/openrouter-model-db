"""Parquet writer with explicit PyArrow schemas for all six tables."""

import pyarrow as pa
import pyarrow.parquet as pq

MODELS_SCHEMA = pa.schema([
    pa.field("slug", pa.string()),
    pa.field("name", pa.string()),
    pa.field("short_name", pa.string()),
    pa.field("author", pa.string()),
    pa.field("description", pa.string()),
    pa.field("context_length", pa.int64()),
    pa.field("group", pa.string()),
    pa.field("input_modalities", pa.list_(pa.string())),
    pa.field("output_modalities", pa.list_(pa.string())),
    pa.field("supports_reasoning", pa.bool_()),
    pa.field("knowledge_cutoff", pa.string()),
    pa.field("permaslug", pa.string()),
    pa.field("hf_slug", pa.string()),
    pa.field("created_at", pa.string()),
    pa.field("updated_at", pa.string()),
    pa.field("warning_message", pa.string()),
    pa.field("default_temperature", pa.float64()),
    pa.field("default_top_p", pa.float64()),
    pa.field("default_top_k", pa.int64()),
    pa.field("default_frequency_penalty", pa.float64()),
    pa.field("default_presence_penalty", pa.float64()),
    pa.field("default_repetition_penalty", pa.float64()),
    pa.field("instruct_type", pa.string()),
    pa.field("tokenizer", pa.string()),
    pa.field("scraped_at", pa.string()),
])

ENDPOINTS_SCHEMA = pa.schema([
    pa.field("endpoint_id", pa.string()),
    pa.field("model_slug", pa.string()),
    pa.field("provider_slug", pa.string()),
    pa.field("endpoint_name", pa.string()),
    pa.field("quantization", pa.string()),
    pa.field("variant", pa.string()),
    pa.field("context_length", pa.int64()),
    pa.field("max_completion_tokens", pa.int64()),
    pa.field("max_prompt_tokens", pa.int64()),
    pa.field("pricing_prompt", pa.string()),
    pa.field("pricing_completion", pa.string()),
    pa.field("pricing_cache_read", pa.string()),
    pa.field("pricing_cache_write", pa.string()),
    pa.field("pricing_image", pa.string()),
    pa.field("pricing_web_search", pa.string()),
    pa.field("pricing_discount", pa.float64()),
    pa.field("long_ctx_threshold", pa.int64()),
    pa.field("long_ctx_prompt_price", pa.string()),
    pa.field("long_ctx_completion_price", pa.string()),
    pa.field("long_ctx_cache_read_price", pa.string()),
    pa.field("uptime_30m", pa.float64()),
    pa.field("latency_p50", pa.float64()),
    pa.field("latency_p75", pa.float64()),
    pa.field("latency_p90", pa.float64()),
    pa.field("latency_p95", pa.float64()),
    pa.field("latency_p99", pa.float64()),
    pa.field("throughput_p50", pa.float64()),
    pa.field("throughput_p75", pa.float64()),
    pa.field("throughput_p90", pa.float64()),
    pa.field("throughput_p95", pa.float64()),
    pa.field("throughput_p99", pa.float64()),
    pa.field("stats_request_count", pa.int64()),
    pa.field("stats_window_minutes", pa.int64()),
    pa.field("is_moderated", pa.bool_()),
    pa.field("is_byok", pa.bool_()),
    pa.field("is_free", pa.bool_()),
    pa.field("supported_parameters", pa.list_(pa.string())),
    pa.field("supports_tool_parameters", pa.bool_()),
    pa.field("supports_reasoning", pa.bool_()),
    pa.field("supports_multipart", pa.bool_()),
    pa.field("provider_region", pa.string()),
    pa.field("scraped_at", pa.string()),
])

PROVIDERS_SCHEMA = pa.schema([
    pa.field("slug", pa.string()),
    pa.field("name", pa.string()),
    pa.field("base_url", pa.string()),
    pa.field("headquarters", pa.string()),
    pa.field("datacenters", pa.list_(pa.string())),
    pa.field("training", pa.bool_()),
    pa.field("training_openrouter", pa.bool_()),
    pa.field("retains_prompts", pa.bool_()),
    pa.field("retention_days", pa.int64()),
    pa.field("can_publish", pa.bool_()),
    pa.field("requires_user_ids", pa.bool_()),
    pa.field("terms_url", pa.string()),
    pa.field("privacy_url", pa.string()),
    pa.field("byok_enabled", pa.bool_()),
    pa.field("is_abortable", pa.bool_()),
    pa.field("moderation_required", pa.bool_()),
    pa.field("adapter_name", pa.string()),
    pa.field("status_page_url", pa.string()),
    pa.field("scraped_at", pa.string()),
])

BENCHMARKS_SCHEMA = pa.schema([
    pa.field("model_slug", pa.string()),
    pa.field("benchmark_name", pa.string()),
    pa.field("score", pa.float64()),
    pa.field("unit", pa.string()),
    pa.field("source", pa.string()),
])

ANALYTICS_SCHEMA = pa.schema([
    pa.field("model_slug", pa.string()),
    pa.field("date", pa.string()),
    pa.field("request_count", pa.int64()),
    pa.field("completion_tokens", pa.int64()),
    pa.field("prompt_tokens", pa.int64()),
    pa.field("reasoning_tokens", pa.int64()),
    pa.field("cached_tokens", pa.int64()),
    pa.field("tool_calls", pa.int64()),
    pa.field("tool_call_errors", pa.int64()),
    pa.field("media_prompt_count", pa.int64()),
    pa.field("media_completion_count", pa.int64()),
    pa.field("audio_prompt_count", pa.int64()),
])

CATEGORIES_SCHEMA = pa.schema([
    pa.field("model_slug", pa.string()),
    pa.field("date", pa.string()),
    pa.field("category", pa.string()),
    pa.field("rank", pa.int64()),
    pa.field("volume", pa.float64()),
    pa.field("request_count", pa.int64()),
    pa.field("prompt_tokens", pa.int64()),
    pa.field("completion_tokens", pa.int64()),
])


def _write(rows: list[dict], schema: pa.Schema, path: str) -> None:
    """Write row dicts to Parquet. Handle empty rows by creating empty table with schema."""
    if not rows:
        table = pa.table(
            {f.name: pa.array([], type=f.type) for f in schema}, schema=schema
        )
    else:
        arrays = {}
        for field in schema:
            values = [row.get(field.name) for row in rows]
            arrays[field.name] = pa.array(values, type=field.type)
        table = pa.table(arrays, schema=schema)
    pq.write_table(table, path)


def write_models(rows, path):
    _write(rows, MODELS_SCHEMA, path)


def write_endpoints(rows, path):
    _write(rows, ENDPOINTS_SCHEMA, path)


def write_providers(rows, path):
    _write(rows, PROVIDERS_SCHEMA, path)


def write_benchmarks(rows, path):
    _write(rows, BENCHMARKS_SCHEMA, path)


def write_analytics(rows, path):
    _write(rows, ANALYTICS_SCHEMA, path)


def write_categories(rows, path):
    _write(rows, CATEGORIES_SCHEMA, path)
