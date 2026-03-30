// Toggle-button facets (multi-select, rendered as pill buttons)
export const MODALITY_FACETS = [
    {
        id: 'input_modalities',
        title: 'Input Modalities',
        column: 'input_modalities',
        values: ['text', 'image', 'file', 'audio', 'video'],
        labels: { text: 'Text', image: 'Image', file: 'File', audio: 'Audio', video: 'Video' },
    },
    {
        id: 'output_modalities',
        title: 'Output Modalities',
        column: 'output_modalities',
        values: ['text', 'image', 'audio'],
        labels: { text: 'Text', image: 'Image', audio: 'Audio' },
    },
];

// Checkbox facets (dynamic values loaded from DB)
export const CHECKBOX_FACETS = [
    { id: 'provider', title: 'Providers', column: 'provider_slug' },
    { id: 'model_group', title: 'Series', column: 'model_group' },
    { id: 'author', title: 'Model Authors', column: 'author' },
    { id: 'category', title: 'Categories', column: 'category', isJoined: true },
    { id: 'supported_params', title: 'Supported Parameters', column: 'supported_params', isArray: true },
];

// Boolean toggle facets
export const BOOLEAN_FACETS = [
    { id: 'reasoning', title: 'Reasoning', column: 'supports_reasoning', label: 'Reasoning models only' },
    { id: 'free', title: 'Free', column: 'is_free', label: 'Free models only' },
    { id: 'tools', title: 'Tools', column: 'tools_support', label: 'Tool calling support' },
];

// Range slider facets
export const RANGE_FACETS = [
    { id: 'context', title: 'Context Length', column: 'context_length', step: 1000 },
    { id: 'price', title: 'Prompt Pricing ($/M)', column: 'input_price_per_m', step: 0.1 },
    { id: 'ttft', title: 'TTFT (ms)', column: 'ttft_ms', step: 10 },
    { id: 'throughput', title: 'Throughput (tok/s)', column: 'tokens_per_sec', step: 5 },
    { id: 'intelligence', title: 'Intelligence Index', column: 'intelligence_index', step: 0.5 },
    { id: 'coding', title: 'Coding Index', column: 'coding_index', step: 0.5 },
    { id: 'agentic', title: 'Agentic Index', column: 'agentic_index', step: 0.5 },
];

export function buildWhereClause(modalityState, checkboxState, booleanState, rangeState) {
    const clauses = [];

    // Modality filters (array contains)
    for (const facet of MODALITY_FACETS) {
        const selected = modalityState[facet.id];
        if (!selected || selected.length === 0) continue;
        // Each selected modality must be present in the array
        for (const val of selected) {
            clauses.push(`list_contains(${facet.column}, '${val}')`);
        }
    }

    // Checkbox filters
    for (const facet of CHECKBOX_FACETS) {
        const state = checkboxState[facet.id];
        if (!state) continue;
        const { checked, all } = state;
        if (checked.length < all.length && checked.length > 0) {
            if (facet.isArray) {
                // Array column — check if any selected value is in the array
                const conditions = checked.map(v => `list_contains(${facet.column}, '${v.replace(/'/g, "''")}')`);
                clauses.push(`(${conditions.join(' OR ')})`);
            } else if (facet.isJoined) {
                // Category — subquery against model_categories table
                const escaped = checked.map(v => `'${v.replace(/'/g, "''")}'`).join(', ');
                clauses.push(`model_slug IN (SELECT model_slug FROM model_categories WHERE category IN (${escaped}))`);
            } else {
                const escaped = checked.map(v => `'${v.replace(/'/g, "''")}'`).join(', ');
                clauses.push(`${facet.column} IN (${escaped})`);
            }
        } else if (checked.length === 0) {
            clauses.push('FALSE');
        }
    }

    // Boolean filters
    for (const facet of BOOLEAN_FACETS) {
        if (booleanState[facet.id]) {
            clauses.push(`${facet.column} = TRUE`);
        }
    }

    // Range filters
    for (const facet of RANGE_FACETS) {
        const state = rangeState[facet.id];
        if (!state) continue;
        if (state.currentMin > state.min) {
            clauses.push(`${facet.column} >= ${state.currentMin}`);
        }
        if (state.currentMax < state.max) {
            clauses.push(`${facet.column} <= ${state.currentMax}`);
        }
    }

    return clauses.length > 0 ? 'WHERE ' + clauses.join(' AND ') : '';
}
