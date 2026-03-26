import pyarrow.parquet as pq
from scraper.parquet import write_models, write_endpoints, write_benchmarks


def test_write_models_roundtrip(tmp_path):
    rows = [{
        "slug": "test/model-1", "name": "Test Model", "short_name": "Model",
        "author": "test", "description": "desc", "context_length": 200000,
        "group": "TestGroup", "input_modalities": ["text", "image"],
        "output_modalities": ["text"], "supports_reasoning": True,
        "knowledge_cutoff": "2025-01-31", "permaslug": "test/model-1-20260318",
        "hf_slug": "", "created_at": "2026-03-18T19:54:03+00:00",
        "updated_at": "2026-03-25T15:39:42+00:00", "warning_message": None,
        "default_temperature": 1.0, "default_top_p": 0.95, "default_top_k": None,
        "default_frequency_penalty": None, "default_presence_penalty": None,
        "default_repetition_penalty": None, "instruct_type": None,
        "tokenizer": "Other", "scraped_at": "2026-03-26T12:00:00+00:00",
    }]
    out = tmp_path / "models.parquet"
    write_models(rows, str(out))
    table = pq.read_table(str(out))
    assert table.num_rows == 1
    assert table.column("slug").to_pylist() == ["test/model-1"]
    assert table.column("input_modalities").to_pylist() == [["text", "image"]]


def test_write_endpoints_roundtrip(tmp_path):
    rows = [{
        "endpoint_id": "abc-123", "model_slug": "test/model-1",
        "provider_slug": "testprovider", "endpoint_name": "TestProvider | test/model-1",
        "quantization": "fp8", "variant": "standard", "context_length": 200000,
        "max_completion_tokens": 32000, "max_prompt_tokens": None,
        "pricing_prompt": "0.000015", "pricing_completion": "0.000075",
        "pricing_cache_read": "0.0000015", "pricing_cache_write": "0.00001875",
        "pricing_image": None, "pricing_web_search": None, "pricing_discount": 0.0,
        "long_ctx_threshold": 128000, "long_ctx_prompt_price": "0.00003",
        "long_ctx_completion_price": "0.00015", "long_ctx_cache_read_price": None,
        "uptime_30m": 100.0, "latency_30m": None, "throughput_30m": None,
        "is_moderated": False, "is_byok": False, "is_free": False,
        "supported_parameters": ["reasoning", "max_tokens", "tools"],
        "supports_tool_parameters": True, "supports_reasoning": True,
        "supports_multipart": True, "provider_region": None,
        "scraped_at": "2026-03-26T12:00:00+00:00",
    }]
    out = tmp_path / "endpoints.parquet"
    write_endpoints(rows, str(out))
    table = pq.read_table(str(out))
    assert table.num_rows == 1
    assert table.column("supported_parameters").to_pylist() == [["reasoning", "max_tokens", "tools"]]


def test_write_benchmarks_roundtrip(tmp_path):
    rows = [{"model_slug": "test/model-1", "benchmark_name": "SWE-bench", "score": 72.5, "unit": "%", "source": "description"}]
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
