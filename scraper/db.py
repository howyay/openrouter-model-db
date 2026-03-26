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
            conn.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM arrow_table"
            )
        conn.close()
    except Exception:
        conn.close()
        raise
