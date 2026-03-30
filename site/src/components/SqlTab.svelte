<script>
    import { onMount } from 'svelte';
    import { TabulatorFull as Tabulator } from 'tabulator-tables';
    import { t } from '../lib/i18n.svelte.js';

    let { queryFn } = $props();

    let inputEl;
    let resultsEl;
    let errorMsg = $state('');
    let resultsTable = null;

    const defaultSql = `SELECT m.name, e.provider_slug, e.latency_p50, e.throughput_p50
FROM model_endpoints e
JOIN models m ON m.slug = e.model_slug
WHERE e.latency_p50 IS NOT NULL
ORDER BY e.latency_p50 ASC
LIMIT 20`;

    async function runQuery() {
        errorMsg = '';
        const sql = inputEl.value.trim();
        if (!sql) return;

        try {
            const rows = await queryFn(sql);
            if (rows.length === 0) {
                errorMsg = 'Query returned 0 rows.';
                if (resultsTable) resultsTable.destroy();
                resultsTable = null;
                return;
            }

            const columns = Object.keys(rows[0]).map(key => ({
                title: key,
                field: key,
                sorter: typeof rows[0][key] === 'number' ? 'number' : 'string',
                headerFilter: "input",
            }));

            if (resultsTable) resultsTable.destroy();
            resultsTable = new Tabulator(resultsEl, {
                data: rows,
                columns,
                height: "100%",
                layout: "fitDataFill",
                placeholder: "No results",
            });
        } catch (e) {
            errorMsg = e.message || String(e);
        }
    }

    function onKeydown(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runQuery();
        }
    }
</script>

<div class="sql-tab">
    <div class="sql-editor">
        <textarea
            bind:this={inputEl}
            class="sql-input"
            spellcheck="false"
            onkeydown={onKeydown}
        >{defaultSql}</textarea>
        <button class="sql-run" onclick={runQuery}>{t('Run (Ctrl+Enter)')}</button>
    </div>
    {#if errorMsg}
        <div class="sql-error">{errorMsg}</div>
    {/if}
    <div class="sql-results" bind:this={resultsEl}></div>
</div>

<style>
    .sql-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .sql-editor {
        padding: 14px;
        display: flex;
        gap: 8px;
        background: var(--bg);
        border-bottom: 1px solid var(--border);
    }

    .sql-input {
        flex: 1;
        min-height: 100px;
        padding: 10px;
        background: var(--bg-surface);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 4px;
        font-family: var(--font-data);
        font-size: 14px;
        resize: vertical;
        line-height: 1.5;
    }

    .sql-input:focus {
        outline: none;
        border-color: var(--accent);
    }

    .sql-run {
        padding: 8px 14px;
        background: var(--accent-muted);
        color: var(--accent);
        border: 1px solid rgba(34, 211, 238, 0.2);
        border-radius: 4px;
        cursor: pointer;
        font-family: var(--font-data);
        font-size: 13px;
        font-weight: 500;
        align-self: flex-end;
        transition: all 0.15s;
    }

    .sql-run:hover {
        background: rgba(34, 211, 238, 0.25);
    }

    .sql-error {
        padding: 10px 14px;
        background: rgba(248, 113, 113, 0.08);
        border-bottom: 1px solid rgba(248, 113, 113, 0.15);
        color: var(--red);
        font-family: var(--font-data);
        font-size: 14px;
    }

    .sql-results { flex: 1; overflow: hidden; }
</style>
