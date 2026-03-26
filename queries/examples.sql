-- ============================================================
-- Example DuckDB queries for the OpenRouter model database
-- Usage: duckdb data/openrouter.duckdb < queries/examples.sql
-- ============================================================

-- All reasoning models sorted by price
SELECT m.name, m.context_length,
       e.pricing_prompt, e.pricing_completion,
       e.provider_slug, e.latency_30m, e.throughput_30m
FROM models m
JOIN model_endpoints e ON m.slug = e.model_slug
WHERE m.supports_reasoning = true
ORDER BY CAST(e.pricing_prompt AS DOUBLE) ASC;

-- Cheapest models with >100k context
SELECT m.name, m.context_length,
       CAST(e.pricing_prompt AS DOUBLE) * 1000000 AS price_per_m_input,
       CAST(e.pricing_completion AS DOUBLE) * 1000000 AS price_per_m_output
FROM models m
JOIN model_endpoints e ON m.slug = e.model_slug
WHERE m.context_length > 100000
ORDER BY price_per_m_input ASC
LIMIT 20;

-- Benchmark leaderboard
SELECT m.name, b.benchmark_name, b.score
FROM model_benchmarks b
JOIN models m ON m.slug = b.model_slug
ORDER BY b.benchmark_name, b.score DESC;

-- Provider data policy comparison
SELECT name, headquarters, training, retains_prompts,
       retention_days, requires_user_ids, byok_enabled
FROM providers
ORDER BY name;

-- Most popular models by request volume (latest day)
SELECT a.model_slug, m.name, a.request_count,
       a.completion_tokens, a.tool_calls
FROM model_analytics a
JOIN models m ON m.slug = a.model_slug
WHERE a.date = (SELECT MAX(date) FROM model_analytics)
ORDER BY a.request_count DESC
LIMIT 20;

-- Top programming models by category rank
SELECT c.model_slug, m.name, c.rank, c.volume
FROM model_categories c
JOIN models m ON m.slug = c.model_slug
WHERE c.category = 'programming'
  AND c.date = (SELECT MAX(date) FROM model_categories)
ORDER BY c.rank ASC;

-- Models that support tool calling
SELECT m.name, e.provider_slug, e.pricing_prompt
FROM models m
JOIN model_endpoints e ON m.slug = e.model_slug
WHERE list_contains(e.supported_parameters, 'tools')
ORDER BY m.name;

-- Free models
SELECT m.name, e.provider_slug, m.context_length
FROM models m
JOIN model_endpoints e ON m.slug = e.model_slug
WHERE e.is_free = true
ORDER BY m.context_length DESC;
