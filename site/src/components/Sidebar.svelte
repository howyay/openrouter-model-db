<script>
    import ModalityFacet from './ModalityFacet.svelte';
    import CheckboxFacet from './CheckboxFacet.svelte';
    import BooleanFacet from './BooleanFacet.svelte';
    import RangeFacet from './RangeFacet.svelte';
    import { t } from '../lib/i18n.svelte.js';
    import {
        MODALITY_FACETS, CHECKBOX_FACETS, BOOLEAN_FACETS, RANGE_FACETS,
        buildWhereClause
    } from '../lib/facets.js';

    const svg = (d) => `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;

    const SECTION_ICONS = {
        // Modality facets
        input_modalities:  svg('<path d="M12 3v18"/><path d="m5 10 7 7 7-7"/>'),
        output_modalities: svg('<path d="M12 21V3"/><path d="m5 14 7-7 7 7"/>'),
        // Checkbox facets
        provider:          svg('<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01"/><path d="M10 10h.01"/><path d="M14 10h.01"/>'),
        model_group:       svg('<path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>'),
        author:            svg('<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
        category:          svg('<path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/><path d="M4 14h6v6H4z"/><path d="M14 14h6v6h-6z"/>'),
        supported_params:  svg('<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>'),
        // Boolean facets
        reasoning:         svg('<path d="M12 2a8 8 0 0 0-8 8c0 3.4 2.1 6.3 5 7.4V20h6v-2.6c2.9-1.1 5-4 5-7.4a8 8 0 0 0-8-8z"/><path d="M10 22h4"/>'),
        free:              svg('<path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/><path d="M18 12a2 2 0 0 0 0 4h4v-4z"/>'),
        tools:             svg('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
        // Range facets
        context:           svg('<path d="M21 6H3"/><path d="M15 12H3"/><path d="M17 18H3"/>'),
        price:             svg('<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'),
        ttft:              svg('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'),
        throughput:        svg('<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'),
        intelligence:      svg('<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>'),
        coding:            svg('<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>'),
        agentic:           svg('<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><path d="M8 16h.01"/><path d="M16 16h.01"/>'),
    };

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
        <div class="loading">{t('Loading filters...')}</div>
    {:else}
        <!-- Modality toggle buttons -->
        {#each MODALITY_FACETS as facet (facet.id)}
            <ModalityFacet
                bind:this={modalityRefs[facet.id]}
                title={t(facet.title)}
                icon={SECTION_ICONS[facet.id]}
                values={facet.values}
                labels={Object.fromEntries(Object.entries(facet.labels).map(([k, v]) => [k, t(v)]))}
                onchange={handleChange}
            />
        {/each}

        <!-- Range sliders (Context, Pricing first like OpenRouter) -->
        {#each rangeData as { facet, min, max } (facet.id)}
            <RangeFacet
                bind:this={rangeRefs[facet.id]}
                title={t(facet.title)}
                icon={SECTION_ICONS[facet.id]}
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
                title={t(facet.title)}
                icon={SECTION_ICONS[facet.id]}
                {values}
                startOpen={true}
                onchange={handleChange}
            />
        {/each}

        <!-- Boolean toggles -->
        {#each BOOLEAN_FACETS as facet (facet.id)}
            <BooleanFacet
                bind:this={booleanRefs[facet.id]}
                title={t(facet.title)}
                icon={SECTION_ICONS[facet.id]}
                label={t(facet.label)}
                onchange={handleChange}
            />
        {/each}
    {/if}
</aside>

<style>
    .sidebar {
        padding: 18px;
        border-right: 1px solid var(--border);
        overflow-y: auto;
        background: var(--bg);
        font-size: 14px;
    }

    .sidebar::-webkit-scrollbar { width: 4px; }
    .sidebar::-webkit-scrollbar-track { background: transparent; }
    .sidebar::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 2px; }

    .loading {
        color: var(--text-dim);
        font-family: var(--font-data);
        font-size: 14px;
    }
</style>
