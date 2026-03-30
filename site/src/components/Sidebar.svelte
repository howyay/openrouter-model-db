<script>
    import ModalityFacet from './ModalityFacet.svelte';
    import CheckboxFacet from './CheckboxFacet.svelte';
    import BooleanFacet from './BooleanFacet.svelte';
    import RangeFacet from './RangeFacet.svelte';
    import {
        MODALITY_FACETS, CHECKBOX_FACETS, BOOLEAN_FACETS, RANGE_FACETS,
        buildWhereClause
    } from '../lib/facets.js';

    let { queryFn, onchange } = $props();

    let checkboxData = $state([]);
    let rangeData = $state([]);
    let loading = $state(true);

    let modalityRefs = {};
    let checkboxRefs = {};
    let booleanRefs = {};
    let rangeRefs = {};

    export async function init() {
        const cbPromises = CHECKBOX_FACETS.map(async (facet) => {
            let rows;
            if (facet.isArray) {
                rows = await queryFn(
                    `SELECT DISTINCT p FROM mega_view, UNNEST(${facet.column}) t(p) WHERE p IS NOT NULL ORDER BY p`
                );
                return { facet, values: rows.map(r => r.p) };
            } else if (facet.isJoined) {
                rows = await queryFn(
                    `SELECT DISTINCT category FROM model_categories ORDER BY category`
                );
                return { facet, values: rows.map(r => r.category) };
            } else {
                rows = await queryFn(
                    `SELECT DISTINCT ${facet.column} FROM mega_view WHERE ${facet.column} IS NOT NULL ORDER BY ${facet.column}`
                );
                return { facet, values: rows.map(r => r[facet.column]) };
            }
        });

        const rangePromises = RANGE_FACETS.map(async (facet) => {
            const stats = await queryFn(
                `SELECT MIN(${facet.column}) AS min_val, MAX(${facet.column}) AS max_val FROM mega_view WHERE ${facet.column} IS NOT NULL`
            );
            if (stats.length && stats[0].min_val != null) {
                return { facet, min: Math.floor(stats[0].min_val), max: Math.ceil(stats[0].max_val) };
            }
            return null;
        });

        const [cbResults, rangeResults] = await Promise.all([
            Promise.all(cbPromises),
            Promise.all(rangePromises),
        ]);

        checkboxData = cbResults;
        rangeData = rangeResults.filter(Boolean);
        loading = false;
    }

    function handleChange() {
        const modalityState = {};
        for (const facet of MODALITY_FACETS) {
            const ref = modalityRefs[facet.id];
            if (ref) {
                modalityState[facet.id] = ref.getSelected();
            }
        }

        const checkboxState = {};
        for (const { facet } of checkboxData) {
            const ref = checkboxRefs[facet.id];
            if (ref) {
                checkboxState[facet.id] = {
                    checked: ref.getChecked(),
                    all: ref.getAll(),
                };
            }
        }

        const booleanState = {};
        for (const facet of BOOLEAN_FACETS) {
            const ref = booleanRefs[facet.id];
            if (ref) {
                booleanState[facet.id] = ref.isChecked();
            }
        }

        const rangeState = {};
        for (const rd of rangeData) {
            const ref = rangeRefs[rd.facet.id];
            if (ref) {
                rangeState[rd.facet.id] = ref.getState();
            }
        }

        const where = buildWhereClause(modalityState, checkboxState, booleanState, rangeState);
        onchange?.(where);
    }
</script>

<aside class="sidebar">
    {#if loading}
        <div class="loading">Loading filters...</div>
    {:else}
        <!-- Modality toggle buttons -->
        {#each MODALITY_FACETS as facet (facet.id)}
            <ModalityFacet
                bind:this={modalityRefs[facet.id]}
                title={facet.title}
                values={facet.values}
                labels={facet.labels}
                onchange={handleChange}
            />
        {/each}

        <!-- Range sliders (Context, Pricing first like OpenRouter) -->
        {#each rangeData as { facet, min, max } (facet.id)}
            <RangeFacet
                bind:this={rangeRefs[facet.id]}
                title={facet.title}
                {min}
                {max}
                step={facet.step}
                onchange={handleChange}
            />
        {/each}

        <!-- Checkbox facets (Providers, Series, Authors, Categories, Params) -->
        {#each checkboxData as { facet, values } (facet.id)}
            <CheckboxFacet
                bind:this={checkboxRefs[facet.id]}
                title={facet.title}
                {values}
                startOpen={true}
                onchange={handleChange}
            />
        {/each}

        <!-- Boolean toggles -->
        {#each BOOLEAN_FACETS as facet (facet.id)}
            <BooleanFacet
                bind:this={booleanRefs[facet.id]}
                title={facet.title}
                label={facet.label}
                onchange={handleChange}
            />
        {/each}
    {/if}
</aside>

<style>
    .sidebar {
        padding: 14px;
        border-right: 1px solid var(--border);
        overflow-y: auto;
        background: var(--bg);
        font-size: 12px;
    }

    .sidebar::-webkit-scrollbar { width: 4px; }
    .sidebar::-webkit-scrollbar-track { background: transparent; }
    .sidebar::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 2px; }

    .loading {
        color: var(--text-dim);
        font-family: var(--font-data);
        font-size: 12px;
    }
</style>
