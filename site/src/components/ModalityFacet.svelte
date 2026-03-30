<script>
    let { title, values, labels = {}, onchange } = $props();

    let selected = $state(new Set());

    export function getSelected() {
        return [...selected];
    }

    function toggle(val) {
        if (selected.has(val)) {
            selected.delete(val);
        } else {
            selected.add(val);
        }
        selected = new Set(selected);
        onchange?.();
    }
</script>

<div class="facet-group">
    <span class="facet-title">{title}</span>
    <div class="pill-row">
        {#each values as val}
            <button
                class="pill"
                class:active={selected.has(val)}
                onclick={() => toggle(val)}
            >
                {labels[val] || val}
            </button>
        {/each}
    </div>
</div>

<style>
    .facet-group { margin-bottom: 14px; }

    .facet-title {
        display: block;
        font-family: var(--font-data);
        font-weight: 500;
        margin-bottom: 6px;
        color: var(--text-dim);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }

    .pill {
        padding: 4px 10px;
        border: 1px solid var(--border);
        border-radius: 12px;
        background: transparent;
        color: var(--text-dim);
        font-family: var(--font-ui);
        font-size: 12px;
        cursor: pointer;
        transition: all 0.15s;
        white-space: nowrap;
    }

    .pill:hover {
        border-color: var(--border-strong);
        color: var(--text-secondary);
    }

    .pill.active {
        background: var(--accent-muted);
        border-color: var(--accent);
        color: var(--accent);
    }
</style>
