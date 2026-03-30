<script>
    import DualRangeSlider from './DualRangeSlider.svelte';

    let { title, min, max, step = 1, onchange } = $props();

    let currentMin = $state(min);
    let currentMax = $state(max);

    export function getState() {
        return { min, max, currentMin, currentMax };
    }
</script>

<div class="facet-group">
    <span class="facet-title">{title}</span>
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
</style>
