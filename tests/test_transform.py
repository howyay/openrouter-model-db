"""Tests for scraper.transform — JSON-to-row transformations."""

from __future__ import annotations

from scraper.transform import (
    transform_analytics,
    transform_categories,
    transform_endpoints,
    transform_model,
    transform_provider,
)

# ---------------------------------------------------------------------------
# Inline test data
# ---------------------------------------------------------------------------

RSC_DATA = {
    "model": {
        "slug": "openai/gpt-4o",
        "name": "GPT-4o",
        "short_name": "GPT-4o",
        "author": "OpenAI",
        "description": "GPT-4o is a multimodal model.",
        "context_length": 128000,
        "group": "openai",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "supports_reasoning": False,
        "knowledge_cutoff": "2024-06",
        "permaslug": "openai/gpt-4o-2024-08-06",
        "hf_slug": None,
        "created_at": "2024-05-13T00:00:00Z",
        "updated_at": "2025-01-10T12:00:00Z",
        "warning_message": None,
        "default_parameters": {
            "temperature": 1.0,
            "top_p": 1.0,
            "top_k": None,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "repetition_penalty": None,
        },
        "architecture": {
            "instruct_type": "none",
            "tokenizer": "GPT",
        },
        "endpoint": {
            "id": "ep-001",
            "provider_slug": "testprovider/fp8",
            "endpoint_name": "Primary",
            "quantization": "fp8",
            "variant": None,
            "context_length": 128000,
            "max_completion_tokens": 16384,
            "max_prompt_tokens": None,
            "pricing": {
                "prompt": "0.0000025",
                "completion": "0.00001",
                "cache_read": "0.00000125",
                "cache_write": "0.0000025",
                "image": "0.003613",
                "web_search": None,
                "discount": 0,
            },
            "variable_pricings": [
                {
                    "type": "prompt-threshold",
                    "threshold": 65536,
                    "prompt": "0.000005",
                    "completion": "0.00002",
                    "cache_read": "0.0000025",
                }
            ],
            "uptime_last_30m": 0.998,
            "latency_30m": 320,
            "throughput_30m": 55.2,
            "moderation_required": False,
            "is_byok": False,
            "is_free": False,
            "supported_parameters": ["temperature", "top_p", "max_tokens"],
            "supports_tool_parameters": True,
            "supports_reasoning": False,
            "supports_multipart": True,
            "provider_region": "US",
            "provider_info": {
                "slug": "testprovider",
                "name": "Test Provider Inc.",
                "baseUrl": "https://api.testprovider.com/v1",
                "headquarters": "San Francisco, CA",
                "datacenters": ["us-east-1", "eu-west-1"],
                "dataPolicy": {
                    "training": False,
                    "training_openrouter": False,
                    "retains_prompts": True,
                    "retention_days": 30,
                    "can_publish": False,
                    "requires_user_ids": False,
                    "terms_url": "https://testprovider.com/terms",
                    "privacy_url": "https://testprovider.com/privacy",
                },
                "byok_enabled": True,
                "is_abortable": True,
                "moderation_required": False,
                "adapterName": "openai",
                "statusPageUrl": "https://status.testprovider.com",
            },
        },
    },
    "variantGroups": [
        [
            {
                "id": "ep-001",
                "provider_slug": "testprovider/fp8",
                "endpoint_name": "Primary",
                "quantization": "fp8",
                "variant": None,
                "context_length": 128000,
                "max_completion_tokens": 16384,
                "max_prompt_tokens": None,
                "pricing": {
                    "prompt": "0.0000025",
                    "completion": "0.00001",
                    "cache_read": "0.00000125",
                    "cache_write": "0.0000025",
                    "image": "0.003613",
                    "web_search": None,
                    "discount": 0,
                },
                "uptime_last_30m": 0.998,
                "latency_30m": 320,
                "throughput_30m": 55.2,
                "moderation_required": False,
                "is_byok": False,
                "is_free": False,
                "supported_parameters": ["temperature", "top_p", "max_tokens"],
                "supports_tool_parameters": True,
                "supports_reasoning": False,
                "supports_multipart": True,
                "provider_region": "US",
            },
            {
                "id": "ep-002",
                "provider_slug": "otherprovider",
                "endpoint_name": "Secondary",
                "quantization": None,
                "variant": "nitro",
                "context_length": 64000,
                "max_completion_tokens": 8192,
                "max_prompt_tokens": 32000,
                "pricing": {
                    "prompt": "0.000003",
                    "completion": "0.000012",
                    "cache_read": None,
                    "cache_write": None,
                    "image": None,
                    "web_search": None,
                    "discount": 0.1,
                },
                "line_items": [
                    {
                        "type": "prompt-threshold",
                        "threshold": 32000,
                        "prompt": "0.000006",
                        "completion": "0.000024",
                        "cache_read": "0.000003",
                    }
                ],
                "uptime_last_30m": 0.995,
                "latency_30m": 450,
                "throughput_30m": 40.0,
                "moderation_required": True,
                "is_byok": True,
                "is_free": False,
                "supported_parameters": ["temperature"],
                "supports_tool_parameters": False,
                "supports_reasoning": False,
                "supports_multipart": False,
                "provider_region": "EU",
            },
        ],
    ],
    "analytics": [
        {
            "date": "2026-03-25 00:00:00",
            "count": 150000,
            "completion_tokens": 5000000,
            "prompt_tokens": 12000000,
            "total_native_tokens_reasoning": 200000,
            "total_native_tokens_cached": 3000000,
            "total_tool_calls": 8000,
            "requests_with_tool_call_errors": 50,
            "media_prompt_count": 1200,
            "media_completion_count": 0,
            "audio_prompt_count": 100,
        },
        {
            "date": "2026-03-26 00:00:00",
            "count": 160000,
            "completion_tokens": 5500000,
            "prompt_tokens": 13000000,
            "total_native_tokens_reasoning": 250000,
            "total_native_tokens_cached": 3200000,
            "total_tool_calls": 9000,
            "requests_with_tool_call_errors": 40,
            "media_prompt_count": 1300,
            "media_completion_count": 10,
            "audio_prompt_count": 110,
        },
    ],
}

CATEGORIES = [
    {
        "date": "2026-03-25",
        "category": "programming",
        "rank": 1,
        "volume": 50000,
        "count": 30000,
        "prompt_tokens": 8000000,
        "completion_tokens": 3000000,
    },
    {
        "date": "2026-03-25",
        "category": "roleplay",
        "rank": 5,
        "volume": 20000,
        "count": 10000,
        "prompt_tokens": 4000000,
        "completion_tokens": 1500000,
    },
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTransformModel:
    def test_basic_fields(self):
        row = transform_model(RSC_DATA)
        assert row["slug"] == "openai/gpt-4o"
        assert row["name"] == "GPT-4o"
        assert row["context_length"] == 128000

    def test_modalities(self):
        row = transform_model(RSC_DATA)
        assert row["input_modalities"] == ["text", "image"]
        assert row["output_modalities"] == ["text"]

    def test_default_parameters(self):
        row = transform_model(RSC_DATA)
        assert row["default_temperature"] == 1.0
        assert row["default_top_p"] == 1.0
        assert row["default_frequency_penalty"] == 0.0

    def test_architecture_fields(self):
        row = transform_model(RSC_DATA)
        assert row["instruct_type"] == "none"
        assert row["tokenizer"] == "GPT"

    def test_scraped_at_present(self):
        row = transform_model(RSC_DATA)
        assert row["scraped_at"] is not None
        assert "T" in row["scraped_at"]


class TestTransformEndpoints:
    def test_count(self):
        rows = transform_endpoints(RSC_DATA)
        assert len(rows) == 2

    def test_endpoint_id_and_model_slug(self):
        rows = transform_endpoints(RSC_DATA)
        assert rows[0]["endpoint_id"] == "ep-001"
        assert rows[0]["model_slug"] == "openai/gpt-4o"

    def test_provider_slug_strip_quantization(self):
        rows = transform_endpoints(RSC_DATA)
        assert rows[0]["provider_slug"] == "testprovider"

    def test_provider_slug_no_quantization(self):
        rows = transform_endpoints(RSC_DATA)
        assert rows[1]["provider_slug"] == "otherprovider"

    def test_pricing_fields(self):
        rows = transform_endpoints(RSC_DATA)
        ep = rows[0]
        assert ep["pricing_prompt"] == "0.0000025"
        assert ep["pricing_completion"] == "0.00001"
        assert ep["pricing_image"] == "0.003613"
        assert ep["pricing_discount"] == 0

    def test_long_ctx_from_variable_pricings(self):
        """ep-001 matches main endpoint which has variable_pricings."""
        rows = transform_endpoints(RSC_DATA)
        ep = rows[0]
        assert ep["long_ctx_threshold"] == 65536
        assert ep["long_ctx_prompt_price"] == "0.000005"
        assert ep["long_ctx_completion_price"] == "0.00002"

    def test_long_ctx_from_line_items(self):
        """ep-002 has line_items directly."""
        rows = transform_endpoints(RSC_DATA)
        ep = rows[1]
        assert ep["long_ctx_threshold"] == 32000
        assert ep["long_ctx_prompt_price"] == "0.000006"
        assert ep["long_ctx_completion_price"] == "0.000024"
        assert ep["long_ctx_cache_read_price"] == "0.000003"

    def test_supported_parameters(self):
        rows = transform_endpoints(RSC_DATA)
        assert rows[0]["supported_parameters"] == ["temperature", "top_p", "max_tokens"]
        assert rows[1]["supported_parameters"] == ["temperature"]

    def test_scraped_at(self):
        rows = transform_endpoints(RSC_DATA)
        assert rows[0]["scraped_at"] is not None

    def test_fallback_to_single_endpoint(self):
        """When variantGroups is absent, use model.endpoint."""
        data = {
            "model": {
                "slug": "test/model",
                "endpoint": {
                    "id": "ep-solo",
                    "provider_slug": "solo",
                    "pricing": {"prompt": "0.001", "completion": "0.002"},
                    "supported_parameters": [],
                },
            },
        }
        rows = transform_endpoints(data)
        assert len(rows) == 1
        assert rows[0]["endpoint_id"] == "ep-solo"


class TestTransformProvider:
    def test_basic_fields(self):
        row = transform_provider(RSC_DATA)
        assert row is not None
        assert row["slug"] == "testprovider"
        assert row["name"] == "Test Provider Inc."
        assert row["headquarters"] == "San Francisco, CA"

    def test_base_url(self):
        row = transform_provider(RSC_DATA)
        assert row["base_url"] == "https://api.testprovider.com/v1"

    def test_datacenters(self):
        row = transform_provider(RSC_DATA)
        assert row["datacenters"] == ["us-east-1", "eu-west-1"]

    def test_data_policy(self):
        row = transform_provider(RSC_DATA)
        assert row["training"] is False
        assert row["retains_prompts"] is True
        assert row["retention_days"] == 30
        assert row["terms_url"] == "https://testprovider.com/terms"
        assert row["privacy_url"] == "https://testprovider.com/privacy"

    def test_adapter_name(self):
        row = transform_provider(RSC_DATA)
        assert row["adapter_name"] == "openai"

    def test_status_page_url(self):
        row = transform_provider(RSC_DATA)
        assert row["status_page_url"] == "https://status.testprovider.com"

    def test_none_when_no_provider_info(self):
        data = {"model": {"endpoint": {}}}
        assert transform_provider(data) is None

    def test_scraped_at(self):
        row = transform_provider(RSC_DATA)
        assert row["scraped_at"] is not None


class TestTransformAnalytics:
    def test_count(self):
        rows = transform_analytics(RSC_DATA)
        assert len(rows) == 2

    def test_model_slug(self):
        rows = transform_analytics(RSC_DATA)
        assert rows[0]["model_slug"] == "openai/gpt-4o"

    def test_date_truncation(self):
        rows = transform_analytics(RSC_DATA)
        assert rows[0]["date"] == "2026-03-25"
        assert rows[1]["date"] == "2026-03-26"

    def test_token_fields(self):
        row = transform_analytics(RSC_DATA)[0]
        assert row["request_count"] == 150000
        assert row["completion_tokens"] == 5000000
        assert row["prompt_tokens"] == 12000000
        assert row["reasoning_tokens"] == 200000
        assert row["cached_tokens"] == 3000000

    def test_tool_fields(self):
        row = transform_analytics(RSC_DATA)[0]
        assert row["tool_calls"] == 8000
        assert row["tool_call_errors"] == 50

    def test_media_fields(self):
        row = transform_analytics(RSC_DATA)[0]
        assert row["media_prompt_count"] == 1200
        assert row["media_completion_count"] == 0
        assert row["audio_prompt_count"] == 100


class TestTransformCategories:
    def test_count(self):
        rows = transform_categories("openai/gpt-4o", CATEGORIES)
        assert len(rows) == 2

    def test_model_slug(self):
        rows = transform_categories("openai/gpt-4o", CATEGORIES)
        assert rows[0]["model_slug"] == "openai/gpt-4o"

    def test_category_and_rank(self):
        rows = transform_categories("openai/gpt-4o", CATEGORIES)
        assert rows[0]["category"] == "programming"
        assert rows[0]["rank"] == 1
        assert rows[1]["category"] == "roleplay"
        assert rows[1]["rank"] == 5

    def test_volume_and_counts(self):
        rows = transform_categories("openai/gpt-4o", CATEGORIES)
        assert rows[0]["volume"] == 50000
        assert rows[0]["request_count"] == 30000
        assert rows[0]["prompt_tokens"] == 8000000
        assert rows[0]["completion_tokens"] == 3000000
