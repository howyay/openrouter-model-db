const CHECKBOX_FACETS = [
    { id: 'provider', title: 'Provider', column: 'provider' },
    { id: 'model_group', title: 'Model Family', column: 'model_group' },
];

const BOOLEAN_FACETS = [
    { id: 'reasoning', title: 'Reasoning', column: 'supports_reasoning', label: 'Reasoning models only' },
    { id: 'free', title: 'Free', column: 'is_free', label: 'Free models only' },
    { id: 'tools', title: 'Tools', column: 'tools_support', label: 'Tool calling support' },
];

const RANGE_FACETS = [
    { id: 'ttft', title: 'TTFT (ms)', column: 'ttft_ms', step: 10 },
    { id: 'throughput', title: 'Throughput (tok/s)', column: 'tokens_per_sec', step: 5 },
    { id: 'intelligence', title: 'Intelligence Index', column: 'intelligence_index', step: 0.5 },
    { id: 'coding', title: 'Coding Index', column: 'coding_index', step: 0.5 },
    { id: 'agentic', title: 'Agentic Index', column: 'agentic_index', step: 0.5 },
    { id: 'context', title: 'Context Length', column: 'context_length', step: 1000 },
    { id: 'price', title: 'Input Price ($/M)', column: 'input_price_per_m', step: 0.1 },
];

let facetState = {};
let onChange = null;

export async function initFacets(containerEl, queryFn, onChangeCb) {
    onChange = onChangeCb;
    containerEl.innerHTML = '';

    for (const facet of CHECKBOX_FACETS) {
        const values = await queryFn(
            `SELECT DISTINCT ${facet.column} FROM mega_view WHERE ${facet.column} IS NOT NULL ORDER BY ${facet.column}`
        );
        const group = document.createElement('div');
        group.className = 'facet-group';
        group.innerHTML = `<label class="facet-title">${facet.title}</label><div class="facet-options" id="facet-${facet.id}"></div>`;
        const optionsEl = group.querySelector('.facet-options');
        for (const row of values) {
            const val = row[facet.column];
            const label = document.createElement('label');
            label.innerHTML = `<input type="checkbox" data-facet="${facet.id}" value="${val}" checked> ${val}`;
            label.querySelector('input').addEventListener('change', _handleChange);
            optionsEl.appendChild(label);
        }
        containerEl.appendChild(group);
    }

    for (const facet of BOOLEAN_FACETS) {
        const group = document.createElement('div');
        group.className = 'facet-group';
        group.innerHTML = `<label class="facet-title">${facet.title}</label>
            <div class="facet-options">
                <label><input type="checkbox" data-facet="${facet.id}"> ${facet.label}</label>
            </div>`;
        group.querySelector('input').addEventListener('change', _handleChange);
        containerEl.appendChild(group);
    }

    for (const facet of RANGE_FACETS) {
        const stats = await queryFn(
            `SELECT MIN(${facet.column}) AS min_val, MAX(${facet.column}) AS max_val FROM mega_view WHERE ${facet.column} IS NOT NULL`
        );
        if (!stats.length || stats[0].min_val == null) continue;
        const min = Math.floor(stats[0].min_val);
        const max = Math.ceil(stats[0].max_val);
        facetState[facet.id] = { min, max, currentMin: min, currentMax: max };

        const group = document.createElement('div');
        group.className = 'facet-group';
        group.innerHTML = `<label class="facet-title">${facet.title}</label>
            <input type="range" id="facet-${facet.id}-min" min="${min}" max="${max}" value="${min}" step="${facet.step}">
            <input type="range" id="facet-${facet.id}-max" min="${min}" max="${max}" value="${max}" step="${facet.step}">
            <div class="range-values"><span id="facet-${facet.id}-min-label">${min}</span><span id="facet-${facet.id}-max-label">${max}</span></div>`;
        group.querySelectorAll('input[type=range]').forEach(el => {
            el.addEventListener('input', (e) => {
                const isMin = e.target.id.endsWith('-min');
                const label = document.getElementById(`facet-${facet.id}-${isMin ? 'min' : 'max'}-label`);
                label.textContent = e.target.value;
                _handleChange();
            });
        });
        containerEl.appendChild(group);
    }
}

function _handleChange() {
    if (onChange) onChange();
}

export function buildWhereClause() {
    const clauses = [];

    for (const facet of CHECKBOX_FACETS) {
        const checkboxes = document.querySelectorAll(`[data-facet="${facet.id}"]`);
        const allChecked = [...checkboxes].filter(cb => cb.checked).map(cb => cb.value);
        const allValues = [...checkboxes].map(cb => cb.value);
        if (allChecked.length < allValues.length && allChecked.length > 0) {
            const escaped = allChecked.map(v => `'${v.replace(/'/g, "''")}'`).join(', ');
            clauses.push(`${facet.column} IN (${escaped})`);
        } else if (allChecked.length === 0) {
            clauses.push('FALSE');
        }
    }

    for (const facet of BOOLEAN_FACETS) {
        const cb = document.querySelector(`[data-facet="${facet.id}"]`);
        if (cb && cb.checked) {
            clauses.push(`${facet.column} = TRUE`);
        }
    }

    for (const facet of RANGE_FACETS) {
        const minEl = document.getElementById(`facet-${facet.id}-min`);
        const maxEl = document.getElementById(`facet-${facet.id}-max`);
        if (!minEl || !maxEl) continue;
        const state = facetState[facet.id];
        if (!state) continue;
        const curMin = parseFloat(minEl.value);
        const curMax = parseFloat(maxEl.value);
        if (curMin > state.min) {
            clauses.push(`${facet.column} >= ${curMin}`);
        }
        if (curMax < state.max) {
            clauses.push(`${facet.column} <= ${curMax}`);
        }
    }

    return clauses.length > 0 ? 'WHERE ' + clauses.join(' AND ') : '';
}
