#!/bin/bash
set -e

echo "Installing duckdb-engine into Superset's Python environment..."
pip install duckdb-engine --target=/app/.venv/lib/python3.10/site-packages

echo "Running database migrations..."
superset db upgrade

echo "Creating admin user..."
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@localhost \
  --password admin || true

echo "Initializing Superset..."
superset init

echo "Starting Superset server..."
exec superset run -h 0.0.0.0 -p 18630 --with-threads --reload
