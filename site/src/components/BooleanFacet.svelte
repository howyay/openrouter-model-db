<script>
    let { title, icon = '', label, onchange } = $props();
    let checked = $state(false);

    export function isChecked() {
        return checked;
    }
</script>

<div class="facet-group">
    <span class="facet-title">
        {#if icon}<span class="title-icon">{@html icon}</span>{/if}
        {title}
    </span>
    <div class="facet-options">
        <label>
            <input
                type="checkbox"
                bind:checked
                onchange={() => onchange?.()}
            >
            {label}
        </label>
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
        font-size: 15px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .title-icon {
        display: flex;
        align-items: center;
        line-height: 0;
    }

    .title-icon :global(svg) {
        flex-shrink: 0;
        opacity: 0.7;
    }

    .facet-options {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }

    .facet-options label {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 6px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 16px;
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
