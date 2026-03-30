<script>
    let { title, label, onchange } = $props();
    let checked = $state(false);

    export function isChecked() {
        return checked;
    }
</script>

<div class="facet-group">
    <span class="facet-title">{title}</span>
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

    .facet-options {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }

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
