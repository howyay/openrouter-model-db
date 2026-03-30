#!/bin/bash
set -e
mkdir -p site/public
cp data/openrouter.duckdb site/public/openrouter.duckdb
cd site
npm run build
echo "Build complete — site/dist/ ready for deploy"
