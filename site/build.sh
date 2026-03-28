#!/bin/bash
set -e
mkdir -p site/public
cp data/openrouter.duckdb site/public/openrouter.duckdb
echo "Build complete — site/ ready for deploy"
