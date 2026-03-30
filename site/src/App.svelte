<script>
    import { onMount } from 'svelte';
    import { initDB, query } from './lib/db.js';
    import { initTheme, cycleTheme, getPreference } from './lib/theme.svelte.js';
    import { t, getLocale, setLocale, LOCALES } from './lib/i18n.svelte.js';
    import Sidebar from './components/Sidebar.svelte';
    import DataTable from './components/DataTable.svelte';
    import SqlTab from './components/SqlTab.svelte';

    let activeTab = $state('explore');

    let loadingMsg = $state('Downloading database...');

    let endpointCount = $state(0);
    let modelCount = $state(0);
    function updateCounts(rows) {
        endpointCount = rows.length;
        modelCount = new Set(rows.map(r => r.model_slug)).size;
    }
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
        updateCounts(rows);
    }

    onMount(async () => {
        initTheme();
        try {
            await initDB('openrouter.duckdb');
            loadingMsg = t('Loading data...');
            initialData = await query(megaQuery());
            updateCounts(initialData);
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
    <h1>{t('OpenRouter Model Explorer')}</h1>
    <nav>
        <button
            class="tab"
            class:active={activeTab === 'explore'}
            onclick={() => activeTab = 'explore'}
        >{t('Explore')}</button>
        <button
            class="tab"
            class:active={activeTab === 'sql'}
            onclick={() => activeTab = 'sql'}
        >{t('SQL')}</button>
        <span class="nav-sep"></span>
        <select class="locale-select" onchange={(e) => setLocale(e.target.value)}>
            {#each LOCALES as loc}
                <option value={loc.code} selected={getLocale() === loc.code}>{loc.label}</option>
            {/each}
        </select>
        <button class="theme-toggle" onclick={cycleTheme} title="Toggle theme">
            {#if getPreference() === 'light'}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            {:else if getPreference() === 'dark'}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            {:else}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            {/if}
        </button>
    </nav>
</header>

{#if loaded}
    <main class="view-explore" class:hidden={activeTab !== 'explore'}>
        <Sidebar bind:this={sidebarRef} queryFn={facetQuery} onchange={onFacetChange} />
        <section class="table-container">
            <DataTable bind:this={tableRef} data={initialData} />
            <div class="status-bar">{endpointCount} {t('endpoints across')} {modelCount} {t('models')}</div>
        </section>
    </main>
    <main class="view-sql" class:hidden={activeTab !== 'sql'}>
        <SqlTab queryFn={query} />
    </main>
{:else}
    <main class="view-explore">
        <div class="loading-full">
            <div class="loading">{t(loadingMsg)}</div>
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
        font-size: 15px;
        font-weight: 500;
        color: var(--text-secondary);
        letter-spacing: 0.02em;
    }

    nav { display: flex; gap: 2px; align-items: center; }

    .nav-sep {
        width: 1px;
        height: 16px;
        background: var(--border-strong);
        margin: 0 6px;
    }

    .theme-toggle {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border: none;
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        cursor: pointer;
        transition: all 0.15s;
    }

    .theme-toggle:hover {
        color: var(--text-secondary);
        background: var(--bg-elevated);
    }

    .tab {
        padding: 6px 12px;
        border: none;
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        cursor: pointer;
        font-family: var(--font-ui);
        font-size: 14px;
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
        font-size: 13px;
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
        font-size: 14px;
    }

    .locale-select {
        padding: 4px 6px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        font-family: var(--font-ui);
        font-size: 12px;
        cursor: pointer;
        outline: none;
        transition: all 0.15s;
    }

    .locale-select:hover {
        color: var(--text-secondary);
        border-color: var(--border-strong);
    }

    .locale-select:focus {
        border-color: var(--accent);
    }

    .locale-select option {
        background: var(--bg-surface);
        color: var(--text);
    }

    .hidden {
        display: none !important;
    }
</style>
