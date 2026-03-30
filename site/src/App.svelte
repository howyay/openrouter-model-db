<script>
    import { onMount } from 'svelte';
    import { initDB, query } from './lib/db.js';
    import { initTheme, setTheme, getPreference } from './lib/theme.svelte.js';
    import { t, getLocale, setLocale, LOCALES } from './lib/i18n.svelte.js';
    import Sidebar from './components/Sidebar.svelte';
    import DataTable from './components/DataTable.svelte';
    import SqlTab from './components/SqlTab.svelte';
    import ThemeIcon from './components/ThemeIcon.svelte';

    let activeTab = $state('explore');

    let loadingMsg = $state('Downloading database...');
    let themeMenuOpen = $state(false);

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
    let themeMenuRef;

    const THEME_OPTIONS = [
        { value: 'system', label: 'System' },
        { value: 'light', label: 'Light' },
        { value: 'dark', label: 'Dark' },
    ];

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

    function getThemeLabel(mode) {
        return THEME_OPTIONS.find((option) => option.value === mode)?.label ?? 'System';
    }

    function toggleThemeMenu() {
        themeMenuOpen = !themeMenuOpen;
    }

    function chooseTheme(mode) {
        setTheme(mode);
        themeMenuOpen = false;
    }

    function onDocumentClick(event) {
        if (themeMenuRef && !themeMenuRef.contains(event.target)) {
            themeMenuOpen = false;
        }
    }

    function onDocumentKeydown(event) {
        if (event.key === 'Escape') {
            themeMenuOpen = false;
        }
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

<svelte:document onclick={onDocumentClick} onkeydown={onDocumentKeydown} />

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
        <div class="theme-menu" bind:this={themeMenuRef}>
            <button
                class="theme-trigger"
                type="button"
                aria-haspopup="menu"
                aria-expanded={themeMenuOpen}
                onclick={(event) => {
                    event.stopPropagation();
                    toggleThemeMenu();
                }}
            >
                <ThemeIcon mode={getPreference()} />
                <span>{getThemeLabel(getPreference())}</span>
                <svg class="theme-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>
            </button>

            {#if themeMenuOpen}
                <div class="theme-popover" role="menu">
                    {#each THEME_OPTIONS as option}
                        <button
                            class="theme-option"
                            class:active={getPreference() === option.value}
                            type="button"
                            role="menuitemradio"
                            aria-checked={getPreference() === option.value}
                            onclick={() => chooseTheme(option.value)}
                        >
                            <ThemeIcon mode={option.value} />
                            <span>{option.label}</span>
                        </button>
                    {/each}
                </div>
            {/if}
        </div>
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
        font-size: 16px;
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

    .tab {
        padding: 6px 12px;
        border: none;
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        cursor: pointer;
        font-family: var(--font-ui);
        font-size: 15px;
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
        grid-template-columns: 300px 1fr;
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
        font-size: 14px;
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
        font-size: 15px;
    }

    .locale-select {
        padding: 4px 6px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        font-family: var(--font-ui);
        font-size: 13px;
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

    .theme-menu {
        position: relative;
    }

    .theme-trigger,
    .theme-option {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        font-family: var(--font-ui);
        font-size: 13px;
        cursor: pointer;
        outline: none;
        transition: all 0.15s;
    }

    .theme-trigger {
        min-width: 104px;
        justify-content: space-between;
        padding: 4px 8px;
    }

    .theme-trigger:hover,
    .theme-option:hover,
    .theme-option.active {
        color: var(--text-secondary);
        border-color: var(--border-strong);
        background: var(--bg-elevated);
    }

    .theme-trigger:focus-visible,
    .theme-option:focus-visible {
        border-color: var(--accent);
    }

    .theme-popover {
        position: absolute;
        top: calc(100% + 6px);
        right: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 132px;
        padding: 6px;
        border: 1px solid var(--border-strong);
        border-radius: 8px;
        background: var(--bg-surface);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
        z-index: 30;
    }

    .theme-option {
        width: 100%;
        padding: 6px 8px;
        border-color: transparent;
        justify-content: flex-start;
    }

    .theme-chevron {
        color: var(--text-dim);
        flex-shrink: 0;
    }

    .hidden {
        display: none !important;
    }
</style>
