<script>
    import { onMount } from 'svelte';
    import { initDB, query } from './lib/db.js';
    import Sidebar from './components/Sidebar.svelte';
    import DataTable from './components/DataTable.svelte';
    import SqlTab from './components/SqlTab.svelte';

    let activeTab = $state('explore');
    let status = $state('');
    let loadingMsg = $state('Downloading database...');
    let loaded = $state(false);

    let initialData = $state([]);
    let sidebarRef;
    let tableRef;

    function megaQuery(where = '', orderBy = 'ORDER BY model, provider') {
        return `SELECT * FROM mega_view ${where} ${orderBy}`;
    }

    function facetQuery(sql) {
        return query(sql);
    }

    async function onFacetChange(where) {
        const rows = await query(megaQuery(where));
        tableRef.replaceData(rows);
        status = `${rows.length} endpoints across ${new Set(rows.map(r => r.model_slug)).size} models`;
    }

    onMount(async () => {
        try {
            await initDB('openrouter.duckdb');
            loadingMsg = 'Loading data...';
            initialData = await query(megaQuery());
            status = `${initialData.length} endpoints across ${new Set(initialData.map(r => r.model_slug)).size} models`;
            loaded = true;

            // Wait a tick for sidebar to mount, then init
            await new Promise(r => setTimeout(r, 0));
            await sidebarRef.init();
        } catch (err) {
            loadingMsg = `Error: ${err.message}`;
            console.error(err);
        }
    });
</script>

<header>
    <h1>OpenRouter Model Explorer</h1>
    <nav>
        <button
            class="tab"
            class:active={activeTab === 'explore'}
            onclick={() => activeTab = 'explore'}
        >Explore</button>
        <button
            class="tab"
            class:active={activeTab === 'sql'}
            onclick={() => activeTab = 'sql'}
        >SQL</button>
    </nav>
</header>

{#if loaded}
    <main class="view-explore" class:hidden={activeTab !== 'explore'}>
        <Sidebar bind:this={sidebarRef} queryFn={facetQuery} onchange={onFacetChange} />
        <section class="table-container">
            <DataTable bind:this={tableRef} data={initialData} />
            <div class="status-bar">{status}</div>
        </section>
    </main>
    <main class="view-sql" class:hidden={activeTab !== 'sql'}>
        <SqlTab queryFn={query} />
    </main>
{:else}
    <main class="view-explore">
        <div class="loading-full">
            <div class="loading">{loadingMsg}</div>
        </div>
    </main>
{/if}

<style>
    header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        height: 48px;
        border-bottom: 1px solid var(--border);
        background: var(--bg);
        flex-shrink: 0;
    }

    header h1 {
        font-family: var(--font-data);
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
        letter-spacing: 0.02em;
    }

    nav { display: flex; gap: 2px; }

    .tab {
        padding: 6px 12px;
        border: none;
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        cursor: pointer;
        font-family: var(--font-ui);
        font-size: 12px;
        font-weight: 500;
        transition: all 0.15s;
    }

    .tab:hover { color: var(--text-secondary); background: var(--bg-elevated); }

    .tab.active {
        background: var(--accent-muted);
        color: var(--accent);
    }

    .view-explore {
        display: grid;
        grid-template-columns: 260px 1fr;
        flex: 1;
        overflow: hidden;
    }

    .table-container {
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .status-bar {
        padding: 6px 16px;
        font-family: var(--font-data);
        font-size: 11px;
        color: var(--text-dim);
        border-top: 1px solid var(--border);
        background: var(--bg);
    }

    .view-sql {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .loading-full {
        grid-column: 1 / -1;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .loading {
        padding: 60px;
        text-align: center;
        color: var(--text-dim);
        font-family: var(--font-data);
        font-size: 12px;
    }

    .hidden {
        display: none !important;
    }
</style>
