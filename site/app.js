import { initDB, query } from './db.js';
import { initFacets, buildWhereClause } from './facets.js';
import { createTable, updateTable } from './table.js';
import { initSqlTab } from './sql-tab.js';

const MEGA_VIEW_SQL = `
SELECT
    m.name AS model,
    m.author,
    m.slug AS model_slug,
    m.context_length,
    m.supports_reasoning,
    m.group AS model_group,
    e.endpoint_id,
    e.provider_slug AS provider,
    e.quantization,
    e.variant,
    e.is_free,
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
`;

async function main() {
    const loadingEl = document.getElementById('loading');
    const statusBar = document.getElementById('status-bar');

    // Init DuckDB
    loadingEl.textContent = 'Downloading database...';
    await initDB('public/openrouter.duckdb');
    loadingEl.textContent = 'Creating view...';

    // Create the mega view
    await query(`CREATE OR REPLACE VIEW mega_view AS ${MEGA_VIEW_SQL}`);

    // Initial data load
    loadingEl.textContent = 'Loading data...';
    const initialData = await query('SELECT * FROM mega_view ORDER BY model, provider');
    loadingEl.classList.add('hidden');

    // Create table
    createTable('#table', initialData);
    statusBar.textContent = `${initialData.length} endpoints across ${new Set(initialData.map(r => r.model_slug)).size} models`;

    // Init facets
    const facetsEl = document.getElementById('facets');
    document.getElementById('facets-loading').remove();
    await initFacets(facetsEl, query, async () => {
        const where = buildWhereClause();
        const sql = `SELECT * FROM mega_view ${where} ORDER BY model, provider`;
        const rows = await query(sql);
        updateTable(rows);
        statusBar.textContent = `${rows.length} endpoints across ${new Set(rows.map(r => r.model_slug)).size} models`;
    });

    // Init SQL tab
    initSqlTab(query);

    // Tab switching
    const tabExplore = document.getElementById('tab-explore');
    const tabSql = document.getElementById('tab-sql');
    const viewExplore = document.getElementById('view-explore');
    const viewSql = document.getElementById('view-sql');

    tabExplore.addEventListener('click', () => {
        tabExplore.classList.add('active');
        tabSql.classList.remove('active');
        viewExplore.classList.remove('hidden');
        viewSql.classList.add('hidden');
    });

    tabSql.addEventListener('click', () => {
        tabSql.classList.add('active');
        tabExplore.classList.remove('active');
        viewSql.classList.remove('hidden');
        viewExplore.classList.add('hidden');
    });
}

main().catch(err => {
    document.getElementById('loading').textContent = `Error: ${err.message}`;
    console.error(err);
});
