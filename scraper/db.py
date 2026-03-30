"""Write row dicts into a DuckDB database file."""

import duckdb
import pyarrow as pa

from scraper.parquet import (
    MODELS_SCHEMA,
    ENDPOINTS_SCHEMA,
    PROVIDERS_SCHEMA,
    BENCHMARKS_SCHEMA,
    ANALYTICS_SCHEMA,
    CATEGORIES_SCHEMA,
)

TABLE_SCHEMAS = {
    "models": MODELS_SCHEMA,
    "model_endpoints": ENDPOINTS_SCHEMA,
    "providers": PROVIDERS_SCHEMA,
    "model_benchmarks": BENCHMARKS_SCHEMA,
    "model_analytics": ANALYTICS_SCHEMA,
    "model_categories": CATEGORIES_SCHEMA,
}


def _to_arrow_table(rows: list[dict], schema: pa.Schema) -> pa.Table:
    """Convert row dicts to a PyArrow table."""
    if not rows:
        return pa.table(
            {f.name: pa.array([], type=f.type) for f in schema}, schema=schema
        )
    arrays = {}
    for field in schema:
        values = [row.get(field.name) for row in rows]
        arrays[field.name] = pa.array(values, type=field.type)
    return pa.table(arrays, schema=schema)


def write_all(db_path: str, table_data: dict[str, list[dict]]) -> None:
    """Write all tables to a DuckDB database file.

    Args:
        db_path: Path to the .duckdb file (created if not exists).
        table_data: Mapping of table name -> list of row dicts.
    """
    conn = duckdb.connect(db_path)
    try:
        for table_name, rows in table_data.items():
            schema = TABLE_SCHEMAS[table_name]
            arrow_table = _to_arrow_table(rows, schema)
            # Drop and recreate to do a full refresh
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM arrow_table")
        conn.execute("DROP TABLE IF EXISTS mega_view")
        conn.execute("""
            CREATE TABLE mega_view AS
            SELECT
                m.name AS model,
                m.author,
                m.slug AS model_slug,
                m.context_length,
                m.supports_reasoning,
                m.group AS model_group,
                m.input_modalities,
                m.output_modalities,
                e.endpoint_id,
                e.provider_slug,
                CASE WHEN e.provider_region IS NOT NULL
                     THEN e.provider_slug || ' (' || e.provider_region || ')'
                     ELSE e.provider_slug
                END AS provider,
                e.quantization,
                e.variant,
                e.is_free,
                e.supported_parameters AS supported_params,
                CAST(e.pricing_prompt AS DOUBLE) * 1000000 AS input_price_per_m,
                CAST(e.pricing_completion AS DOUBLE) * 1000000 AS output_price_per_m,
                e.latency_p50 AS ttft_ms,
                e.latency_p95 AS ttft_p95_ms,
                e.throughput_p50 AS tokens_per_sec,
                e.throughput_p95 AS tokens_per_sec_p95,
                e.uptime_30m AS uptime_pct,
                e.stats_request_count AS recent_requests,
                e.supports_tool_parameters AS tools_support,
                b.intelligence_index,
                b.coding_index,
                b.agentic_index,
                b.intelligence_percentile AS intelligence_pct,
                b.coding_percentile AS coding_pct,
                b.agentic_percentile AS agentic_pct,
                b.aa_name AS benchmark_config
            FROM model_endpoints e
            JOIN models m ON m.slug = e.model_slug
            LEFT JOIN (
                SELECT * FROM (
                    SELECT *,
                        ROW_NUMBER() OVER (
                            PARTITION BY model_slug
                            ORDER BY
                                CASE
                                    WHEN aa_name ILIKE '%medium%' THEN 1
                                    WHEN aa_name ILIKE '%reasoning%'
                                         AND aa_name NOT ILIKE '%non-reasoning%'
                                         AND aa_name NOT ILIKE '%max%'
                                         AND aa_name NOT ILIKE '%high%'
                                         AND aa_name NOT ILIKE '%low%'
                                         AND aa_name NOT ILIKE '%minimal%' THEN 2
                                    WHEN aa_name NOT ILIKE '%non-reasoning%'
                                         AND aa_name NOT ILIKE '%max%'
                                         AND aa_name NOT ILIKE '%xhigh%' THEN 3
                                    ELSE 4
                                END,
                                intelligence_index DESC NULLS LAST
                        ) AS rn
                    FROM model_benchmarks
                    WHERE intelligence_index IS NOT NULL
                ) ranked WHERE rn = 1
            ) b ON b.model_slug = m.slug
        """)
        conn.close()
    except Exception:
        conn.close()
        raise
