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
    let mobileFiltersOpen = $state(false);
    let isMobile = $state(false);

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
            mobileFiltersOpen = false;
        }
    }

    function updateViewportState() {
        isMobile = window.innerWidth <= 820;
        if (!isMobile) {
            mobileFiltersOpen = false;
        }
    }

    function toggleMobileFilters() {
        mobileFiltersOpen = !mobileFiltersOpen;
    }

    function closeMobileFilters() {
        mobileFiltersOpen = false;
    }

    onMount(async () => {
        initTheme();
        updateViewportState();
        window.addEventListener('resize', updateViewportState);
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

        return () => {
            window.removeEventListener('resize', updateViewportState);
        };
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
        {#if isMobile && activeTab === 'explore'}
            <button class="filters-trigger" type="button" onclick={toggleMobileFilters}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18"/><path d="M6 12h12"/><path d="M10 18h4"/></svg>
                <span>Filters</span>
            </button>
        {/if}
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
        <button class="sidebar-backdrop" class:open={isMobile && mobileFiltersOpen} type="button" aria-label="Close filters" onclick={closeMobileFilters}></button>
        <div class="sidebar-shell" class:mobile-open={isMobile && mobileFiltersOpen}>
            <div class="sidebar-mobile-header">
                <strong>Filters</strong>
                <button type="button" class="sidebar-close" onclick={closeMobileFilters} aria-label="Close filters">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
            </div>
            <Sidebar bind:this={sidebarRef} queryFn={facetQuery} onchange={onFacetChange} />
        </div>
        <section class="table-container">
            {#if isMobile}
                <div class="table-mobile-hint">Swipe the table horizontally for more columns.</div>
            {/if}
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

    .filters-trigger {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background: transparent;
        color: var(--text-dim);
        cursor: pointer;
        font-family: var(--font-ui);
        font-size: 14px;
        font-weight: 500;
        transition: all 0.15s;
    }

    .filters-trigger:hover {
        color: var(--text-secondary);
        border-color: var(--border-strong);
        background: var(--bg-elevated);
    }

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
        min-width: 0;
    }

    .table-mobile-hint {
        display: none;
        padding: 8px 14px;
        border-bottom: 1px solid var(--border);
        background: var(--bg-surface);
        color: var(--text-dim);
        font-size: 13px;
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

    .sidebar-backdrop,
    .sidebar-mobile-header {
        display: none;
    }

    .sidebar-shell {
        display: block;
        min-width: 0;
        overflow: hidden;
    }

    :global(.sidebar-shell .sidebar) {
        height: 100%;
    }

    .hidden {
        display: none !important;
    }

    @media (max-width: 980px) {
        header {
            height: auto;
            padding: 10px 14px;
            align-items: flex-start;
            gap: 10px;
            flex-direction: column;
        }

        nav {
            width: 100%;
            flex-wrap: wrap;
            gap: 8px;
        }

        .nav-sep {
            display: none;
        }
    }

    @media (max-width: 820px) {
        .view-explore {
            grid-template-columns: 1fr;
        }

        .sidebar-shell {
            position: fixed;
            inset: 0 auto 0 0;
            width: min(88vw, 360px);
            background: var(--bg);
            border-right: 1px solid var(--border-strong);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
            transform: translateX(-100%);
            transition: transform 180ms ease;
            z-index: 40;
            display: flex;
            flex-direction: column;
        }

        .sidebar-shell.mobile-open {
            transform: translateX(0);
        }

        .sidebar-backdrop {
            position: fixed;
            inset: 0;
            display: block;
            border: 0;
            background: rgba(0, 0, 0, 0.45);
            opacity: 0;
            pointer-events: none;
            transition: opacity 180ms ease;
            z-index: 30;
        }

        .sidebar-backdrop.open {
            opacity: 1;
            pointer-events: auto;
        }

        .sidebar-mobile-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            background: var(--bg);
            font-size: 14px;
        }

        .sidebar-close {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: transparent;
            color: var(--text-dim);
            cursor: pointer;
        }

        .table-mobile-hint {
            display: block;
        }

        :global(.sidebar-shell .sidebar) {
            flex: 1;
            min-height: 0;
            border-right: 0;
        }
    }

    @media (max-width: 640px) {
        header h1 {
            font-size: 15px;
        }

        .tab,
        .filters-trigger {
            font-size: 14px;
        }

        .locale-select {
            max-width: 46vw;
        }

        .theme-trigger {
            min-width: auto;
            padding: 4px 7px;
        }

        .theme-trigger span {
            display: none;
        }

        .status-bar {
            font-size: 13px;
            padding: 6px 12px;
        }
    }
</style>
