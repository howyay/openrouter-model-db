"""Tests for scraper.rsc — RSC payload extraction."""

from __future__ import annotations

from scraper.rsc import extract_rsc_categories, extract_rsc_model_data


# ── Model data extraction ────────────────────────────────────────────


def test_extract_rsc_model_data_returns_model_dict(SAMPLE_RSC_HTML: str) -> None:
    data = extract_rsc_model_data(SAMPLE_RSC_HTML)
    assert data is not None
    model = data["model"]
    assert model["slug"] == "test/model-1"
    assert model["name"] == "Test: Model-1"
    assert model["context_length"] == 1048576


def test_extract_rsc_model_data_includes_endpoint(SAMPLE_RSC_HTML: str) -> None:
    data = extract_rsc_model_data(SAMPLE_RSC_HTML)
    assert data is not None
    ep = data["model"]["endpoint"]
    assert ep["id"] == "abc-123"
    assert ep["provider_name"] == "TestProvider"
    assert ep["quantization"] == "fp8"


def test_extract_rsc_model_data_includes_provider_info(SAMPLE_RSC_HTML: str) -> None:
    data = extract_rsc_model_data(SAMPLE_RSC_HTML)
    assert data is not None
    info = data["model"]["endpoint"]["provider_info"]
    assert info["headquarters"] == "US"
    assert info["datacenters"] == ["US", "EU"]
    assert info["dataPolicy"]["retentionDays"] == 30


def test_extract_rsc_model_data_includes_analytics(SAMPLE_RSC_HTML: str) -> None:
    data = extract_rsc_model_data(SAMPLE_RSC_HTML)
    assert data is not None
    analytics = data["analytics"]
    assert len(analytics) == 1
    assert analytics[0]["count"] == 2037879
    assert analytics[0]["total_completion_tokens"] == 870654946


def test_extract_rsc_model_data_includes_variant_groups(SAMPLE_RSC_HTML: str) -> None:
    data = extract_rsc_model_data(SAMPLE_RSC_HTML)
    assert data is not None
    vg = data["variantGroups"]
    assert len(vg) == 1
    assert vg[0]["variant"] == "standard"
    assert len(vg[0]["endpoints"]) == 1


# ── Categories extraction ────────────────────────────────────────────


def test_extract_rsc_categories(SAMPLE_RSC_HTML: str) -> None:
    cats = extract_rsc_categories(SAMPLE_RSC_HTML)
    assert len(cats) == 2
    names = {c["category"] for c in cats}
    assert names == {"programming", "technology"}
    prog = next(c for c in cats if c["category"] == "programming")
    assert prog["rank"] == 1
    tech = next(c for c in cats if c["category"] == "technology")
    assert tech["rank"] == 3


# ── Edge cases ───────────────────────────────────────────────────────


def test_extract_rsc_model_data_returns_none_for_no_data() -> None:
    assert extract_rsc_model_data("<html></html>") is None


def test_extract_rsc_categories_returns_empty_for_no_data() -> None:
    assert extract_rsc_categories("<html></html>") == []
