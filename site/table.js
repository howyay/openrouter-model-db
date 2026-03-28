let table = null;

const COLUMNS = [
    {
        title: "Provider", field: "provider", sorter: "string",
        headerFilter: "input", headerFilterPlaceholder: "Filter...",
        width: 130,
    },
    {
        title: "TTFT (ms)", field: "ttft_ms", sorter: "number",
        hozAlign: "right", width: 100,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "Tok/s", field: "tokens_per_sec", sorter: "number",
        hozAlign: "right", width: 80,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "$/M in", field: "input_price_per_m", sorter: "number",
        hozAlign: "right", width: 80,
        formatter: (cell) => {
            const v = cell.getValue();
            if (v == null) return '—';
            return v < 0.01 ? 'Free' : '$' + v.toFixed(2);
        },
    },
    {
        title: "$/M out", field: "output_price_per_m", sorter: "number",
        hozAlign: "right", width: 80,
        formatter: (cell) => {
            const v = cell.getValue();
            if (v == null) return '—';
            return v < 0.01 ? 'Free' : '$' + v.toFixed(2);
        },
    },
    {
        title: "Intel", field: "intelligence_index", sorter: "number",
        hozAlign: "right", width: 70,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) : '—';
        },
    },
    {
        title: "Code", field: "coding_index", sorter: "number",
        hozAlign: "right", width: 70,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) : '—';
        },
    },
    {
        title: "Agent", field: "agentic_index", sorter: "number",
        hozAlign: "right", width: 70,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) : '—';
        },
    },
    {
        title: "Context", field: "context_length", sorter: "number",
        hozAlign: "right", width: 90, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? (v / 1000).toFixed(0) + 'k' : '—';
        },
    },
    {
        title: "Reasoning", field: "supports_reasoning", sorter: "boolean",
        hozAlign: "center", width: 90, visible: false,
        formatter: "tickCross",
    },
    {
        title: "Quant", field: "quantization", sorter: "string",
        width: 80, visible: false,
    },
    {
        title: "Uptime", field: "uptime_pct", sorter: "number",
        hozAlign: "right", width: 80, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toFixed(1) + '%' : '—';
        },
    },
    {
        title: "TTFT p95", field: "ttft_p95_ms", sorter: "number",
        hozAlign: "right", width: 100, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "Tok/s p95", field: "tokens_per_sec_p95", sorter: "number",
        hozAlign: "right", width: 90, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? Math.round(v).toLocaleString() : '—';
        },
    },
    {
        title: "Requests", field: "recent_requests", sorter: "number",
        hozAlign: "right", width: 90, visible: false,
        formatter: (cell) => {
            const v = cell.getValue();
            return v != null ? v.toLocaleString() : '—';
        },
    },
    {
        title: "Benchmark", field: "benchmark_config", sorter: "string",
        width: 150, visible: false,
    },
];

export function createTable(containerEl, data) {
    table = new Tabulator(containerEl, {
        data: data,
        height: "100%",
        layout: "fitDataFill",
        groupBy: "model",
        groupStartOpen: true,
        groupToggleElement: "header",
        groupHeader: (value, count) => {
            return `<span style="font-weight:600">${value}</span> <span style="opacity:0.5">(${count} provider${count !== 1 ? 's' : ''})</span>`;
        },
        columns: COLUMNS,
        initialSort: [
            { column: "model", dir: "asc" },
            { column: "ttft_ms", dir: "asc" },
        ],
        placeholder: "No matching models",
    });
    return table;
}

export function updateTable(data) {
    if (table) {
        table.replaceData(data);
    }
}

export function getRowCount() {
    return table ? table.getDataCount() : 0;
}
