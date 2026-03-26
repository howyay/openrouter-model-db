"""Transform nested RSC JSON dicts into flat row dicts for Parquet tables."""

from __future__ import annotations

from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def transform_model(rsc_data: dict) -> dict:
    """Extract a flat model row from *rsc_data*."""
    m = rsc_data.get("model", {})
    arch = m.get("architecture", {})
    defaults = m.get("default_parameters") or {}

    return {
        "slug": m.get("slug"),
        "name": m.get("name"),
        "short_name": m.get("short_name"),
        "author": m.get("author"),
        "description": m.get("description"),
        "context_length": m.get("context_length"),
        "group": m.get("group"),
        "input_modalities": m.get("input_modalities", []),
        "output_modalities": m.get("output_modalities", []),
        "supports_reasoning": m.get("supports_reasoning"),
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
        "tokenizer": m.get("tokenizer") or arch.get("tokenizer"),
        "scraped_at": _now_iso(),
    }


def transform_endpoints(rsc_data: dict) -> list[dict]:
    """Extract flat endpoint rows from *rsc_data*."""
    model = rsc_data.get("model", {})
    model_slug = model.get("slug")
    main_endpoint = model.get("endpoint", {})

    variant_groups = rsc_data.get("variantGroups", [])

    # Collect raw endpoint dicts
    raw_endpoints: list[dict] = []
    for group in variant_groups:
        endpoints = group if isinstance(group, list) else group.get("endpoints", [])
        for ep in endpoints:
            raw_endpoints.append(ep)

    if not raw_endpoints and main_endpoint:
        raw_endpoints.append(main_endpoint)

    rows: list[dict] = []
    for ep in raw_endpoints:
        pricing = ep.get("pricing", {})
        provider_slug_raw = ep.get("provider_slug", "") or ""
        # Strip quantization suffix: "testprovider/fp8" -> "testprovider"
        provider_slug = provider_slug_raw.split("/")[0] if "/" in provider_slug_raw else provider_slug_raw

        # Long-context pricing: check variable_pricings or line_items
        long_ctx_threshold = None
        long_ctx_prompt_price = None
        long_ctx_completion_price = None
        long_ctx_cache_read_price = None

        source_ep = ep
        # If this endpoint comes from variantGroups and lacks pricing details,
        # fall back to main endpoint when IDs match.
        if ep.get("id") and ep.get("id") == main_endpoint.get("id"):
            source_ep = main_endpoint

        vp = source_ep.get("variable_pricings") or ep.get("variable_pricings")
        li = source_ep.get("line_items") or ep.get("line_items")

        if vp:
            for vp_item in vp:
                if vp_item.get("type") == "prompt-threshold":
                    long_ctx_threshold = vp_item.get("threshold")
                    long_ctx_prompt_price = vp_item.get("prompt")
                    long_ctx_completion_price = vp_item.get("completion")
                    long_ctx_cache_read_price = vp_item.get("cache_read")
                    break
        elif li:
            for li_item in li:
                if li_item.get("type") == "prompt-threshold":
                    long_ctx_threshold = li_item.get("threshold")
                    long_ctx_prompt_price = li_item.get("prompt")
                    long_ctx_completion_price = li_item.get("completion")
                    long_ctx_cache_read_price = li_item.get("cache_read")
                    break

        rows.append({
            "endpoint_id": ep.get("id"),
            "model_slug": model_slug,
            "provider_slug": provider_slug,
            "endpoint_name": ep.get("endpoint_name") or ep.get("name"),
            "quantization": ep.get("quantization"),
            "variant": ep.get("variant"),
            "context_length": ep.get("context_length"),
            "max_completion_tokens": ep.get("max_completion_tokens"),
            "max_prompt_tokens": ep.get("max_prompt_tokens"),
            "pricing_prompt": pricing.get("prompt"),
            "pricing_completion": pricing.get("completion"),
            "pricing_cache_read": pricing.get("cache_read"),
            "pricing_cache_write": pricing.get("cache_write"),
            "pricing_image": pricing.get("image"),
            "pricing_web_search": pricing.get("web_search"),
            "pricing_discount": pricing.get("discount"),
            "long_ctx_threshold": long_ctx_threshold,
            "long_ctx_prompt_price": long_ctx_prompt_price,
            "long_ctx_completion_price": long_ctx_completion_price,
            "long_ctx_cache_read_price": long_ctx_cache_read_price,
            "uptime_30m": ep.get("uptime_last_30m"),
            "latency_30m": ep.get("latency_30m"),
            "throughput_30m": ep.get("throughput_30m"),
            "is_moderated": ep.get("moderation_required"),
            "is_byok": ep.get("is_byok"),
            "is_free": ep.get("is_free"),
            "supported_parameters": ep.get("supported_parameters"),
            "supports_tool_parameters": ep.get("supports_tool_parameters"),
            "supports_reasoning": ep.get("supports_reasoning"),
            "supports_multipart": ep.get("supports_multipart"),
            "provider_region": ep.get("provider_region"),
            "scraped_at": _now_iso(),
        })

    return rows


def transform_provider(rsc_data: dict) -> dict | None:
    """Extract a flat provider row from *rsc_data*, or None if absent."""
    model = rsc_data.get("model", {})
    endpoint = model.get("endpoint", {})
    info = endpoint.get("provider_info")
    if not info:
        return None

    policy = info.get("dataPolicy", {})

    return {
        "slug": info.get("slug"),
        "name": info.get("name"),
        "base_url": info.get("baseUrl"),
        "headquarters": info.get("headquarters"),
        "datacenters": info.get("datacenters", []),
        "training": policy.get("training"),
        "training_openrouter": policy.get("training_openrouter"),
        "retains_prompts": policy.get("retains_prompts"),
        "retention_days": policy.get("retention_days"),
        "can_publish": policy.get("can_publish"),
        "requires_user_ids": policy.get("requires_user_ids"),
        "terms_url": policy.get("terms_url"),
        "privacy_url": policy.get("privacy_url"),
        "byok_enabled": info.get("byok_enabled"),
        "is_abortable": info.get("is_abortable"),
        "moderation_required": info.get("moderation_required"),
        "adapter_name": info.get("adapterName"),
        "status_page_url": info.get("statusPageUrl"),
        "scraped_at": _now_iso(),
    }


def transform_analytics(rsc_data: dict) -> list[dict]:
    """Extract flat analytics rows from *rsc_data*."""
    model_slug = rsc_data.get("model", {}).get("slug")
    analytics = rsc_data.get("analytics", [])
    rows: list[dict] = []

    for entry in analytics:
        raw_date = entry.get("date", "")
        # Truncate "2026-03-26 00:00:00" to "2026-03-26"
        date = raw_date[:10] if raw_date else raw_date

        rows.append({
            "model_slug": model_slug,
            "date": date,
            "request_count": entry.get("count"),
            "completion_tokens": entry.get("completion_tokens"),
            "prompt_tokens": entry.get("prompt_tokens"),
            "reasoning_tokens": entry.get("total_native_tokens_reasoning"),
            "cached_tokens": entry.get("total_native_tokens_cached"),
            "tool_calls": entry.get("total_tool_calls"),
            "tool_call_errors": entry.get("requests_with_tool_call_errors"),
            "media_prompt_count": entry.get("media_prompt_count"),
            "media_completion_count": entry.get("media_completion_count"),
            "audio_prompt_count": entry.get("audio_prompt_count"),
        })

    return rows


def transform_categories(model_slug: str, categories: list[dict]) -> list[dict]:
    """Extract flat category rows from a categories array."""
    rows: list[dict] = []
    for cat in categories:
        rows.append({
            "model_slug": model_slug,
            "date": cat.get("date"),
            "category": cat.get("category"),
            "rank": cat.get("rank"),
            "volume": cat.get("volume"),
            "request_count": cat.get("count"),
            "prompt_tokens": cat.get("prompt_tokens"),
            "completion_tokens": cat.get("completion_tokens"),
        })
    return rows
