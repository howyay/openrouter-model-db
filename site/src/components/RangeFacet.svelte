<script>
    import DualRangeSlider from './DualRangeSlider.svelte';

    let { title, icon = '', min, max, step = 1, onchange } = $props();

    let currentMin = $state(min);
    let currentMax = $state(max);

    export function getState() {
        return { min, max, currentMin, currentMax };
    }
</script>

<div class="facet-group">
    <span class="facet-title">
        {#if icon}<span class="title-icon">{@html icon}</span>{/if}
        {title}
    </span>
    <DualRangeSlider
        {min}
        {max}
        {step}
        bind:currentMin
        bind:currentMax
        {onchange}
    />
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

    .title-icon {
        display: flex;
        align-items: center;
        line-height: 0;
    }

    .title-icon :global(svg) {
        flex-shrink: 0;
        opacity: 0.7;
    }
</style>
