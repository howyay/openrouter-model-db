<script>
    let { title, values, startOpen = true, onchange } = $props();

    let open = $state(startOpen);
    let checked = $state(new Set(values));
    let search = $state('');

    let filtered = $derived(
        search
            ? values.filter(v => v.toLowerCase().includes(search.toLowerCase()))
            : values
    );

    export function getChecked() {
        return [...checked];
    }

    export function getAll() {
        return values;
    }

    function toggle(val) {
        if (checked.has(val)) {
            checked.delete(val);
        } else {
            checked.add(val);
        }
        checked = new Set(checked);
        onchange?.();
    }

    function selectAll() {
        checked = new Set(values);
        onchange?.();
    }

    function selectNone() {
        checked = new Set();
        onchange?.();
    }
</script>

<div class="facet-group">
    <button class="facet-title" onclick={() => open = !open}>
        <span class="chevron" class:open>▶</span>
        {title}
        {#if checked.size < values.length}
            <span class="badge">{checked.size}/{values.length}</span>
        {/if}
    </button>
    {#if open}
        {#if values.length > 8}
            <input
                class="facet-search"
                type="text"
                placeholder="Search..."
                bind:value={search}
            >
        {/if}
        <div class="facet-actions">
            <button onclick={selectAll}>All</button>
            <button onclick={selectNone}>None</button>
        </div>
        <div class="facet-options">
            {#each filtered as val}
                <label>
                    <input
                        type="checkbox"
                        checked={checked.has(val)}
                        onchange={() => toggle(val)}
                    >
                    {val}
                </label>
            {/each}
        </div>
    {/if}
</div>

<style>
    .facet-group { margin-bottom: 14px; }

    .facet-title {
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
        background: none;
        border: none;
        cursor: pointer;
        font-family: var(--font-data);
        font-weight: 500;
        margin-bottom: 6px;
        color: var(--text-dim);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 2px 0;
    }

    .facet-title:hover { color: var(--text-secondary); }

    .chevron {
        font-size: 8px;
        transition: transform 0.15s;
        flex-shrink: 0;
    }

    .chevron.open { transform: rotate(90deg); }

    .badge {
        margin-left: auto;
        font-size: 10px;
        color: var(--accent);
        font-weight: 400;
    }

    .facet-search {
        width: 100%;
        padding: 4px 8px;
        margin-bottom: 4px;
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 4px;
        color: var(--text);
        font-family: var(--font-data);
        font-size: 11px;
        outline: none;
    }

    .facet-search:focus {
        border-color: var(--accent);
    }

    .facet-actions {
        display: flex;
        gap: 8px;
        margin-bottom: 4px;
    }

    .facet-actions button {
        background: none;
        border: none;
        color: var(--text-dim);
        font-family: var(--font-data);
        font-size: 10px;
        cursor: pointer;
        padding: 0;
        text-decoration: underline;
        text-underline-offset: 2px;
    }

    .facet-actions button:hover {
        color: var(--accent);
    }

    .facet-options {
        display: flex;
        flex-direction: column;
        gap: 1px;
        max-height: 180px;
        overflow-y: auto;
    }

    .facet-options::-webkit-scrollbar { width: 4px; }
    .facet-options::-webkit-scrollbar-track { background: transparent; }
    .facet-options::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 2px; }

    .facet-options label {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 4px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 13px;
        color: var(--text-secondary);
        transition: all 0.1s;
    }

    .facet-options label:hover {
        color: var(--text);
        background: var(--bg-elevated);
    }

    .facet-options input[type="checkbox"] {
        accent-color: var(--accent);
        width: 14px;
        height: 14px;
    }
</style>
