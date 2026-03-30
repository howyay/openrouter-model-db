<script>
    let { title, icon = '', values, labels = {}, onchange } = $props();

    let selected = $state(new Set());

    const MODALITY_ICONS = {
        text: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h10"/></svg>`,
        image: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>`,
        file: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>`,
        audio: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10v3a2 2 0 0 0 2 2h3l5 4V3L7 7H4a2 2 0 0 0-2 2Z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>`,
        video: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.934a.5.5 0 0 0-.777-.416L16 11"/><rect x="2" y="6" width="14" height="12" rx="2"/></svg>`,
    };

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
    <span class="facet-title">
        {#if icon}{@html icon}{/if}
        {title}
    </span>
    <div class="pill-row">
        {#each values as val}
            <button
                class="pill"
                class:active={selected.has(val)}
                onclick={() => toggle(val)}
            >
                {#if MODALITY_ICONS[val]}<span class="pill-icon">{@html MODALITY_ICONS[val]}</span>{/if}
                {labels[val] || val}
            </button>
        {/each}
    </div>
</div>

<style>
    .facet-group { margin-bottom: 18px; }

    .facet-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: var(--font-data);
        font-weight: 500;
        margin-bottom: 6px;
        color: var(--text-dim);
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .facet-title :global(svg) {
        flex-shrink: 0;
        opacity: 0.7;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 5px 10px;
        border: 1px solid var(--border);
        border-radius: 12px;
        background: transparent;
        color: var(--text-dim);
        font-family: var(--font-ui);
        font-size: 14px;
        cursor: pointer;
        transition: all 0.15s;
        white-space: nowrap;
    }

    .pill-icon {
        display: flex;
        align-items: center;
        line-height: 0;
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
