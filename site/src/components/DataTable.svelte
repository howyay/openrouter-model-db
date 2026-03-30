<script>
    import { onMount } from 'svelte';
    import 'tabulator-tables/dist/css/tabulator.min.css';
    import { TabulatorFull as Tabulator } from 'tabulator-tables';

    let { data = [] } = $props();

    let containerEl;
    let table = null;

    const num = (cell) => {
        const v = cell.getValue();
        return v != null ? Math.round(v).toLocaleString() : '<span style="color:#52525b">—</span>';
    };

    const COLUMNS = [
        {
            title: "Provider", field: "provider", sorter: "string",
            headerFilter: "input", headerFilterPlaceholder: "filter...",
            minWidth: 100, widthGrow: 2,
        },
        {
            title: "TTFT", field: "ttft_ms", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1,
            formatter: num,
        },
        {
            title: "Tok/s", field: "tokens_per_sec", sorter: "number",
            hozAlign: "right", minWidth: 60, widthGrow: 1,
            formatter: num,
        },
        {
            title: "$/M in", field: "input_price_per_m", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '<span style="color:#52525b">—</span>';
                return v < 0.01 ? '<span style="color:#4ade80">Free</span>' : '$' + v.toFixed(2);
            },
        },
        {
            title: "$/M out", field: "output_price_per_m", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '<span style="color:#52525b">—</span>';
                return v < 0.01 ? '<span style="color:#4ade80">Free</span>' : '$' + v.toFixed(2);
            },
        },
        {
            title: "Intel", field: "intelligence_index", sorter: "number",
            hozAlign: "right", minWidth: 55, widthGrow: 1,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? v.toFixed(1) : '<span style="color:#52525b">—</span>';
            },
        },
        {
            title: "Code", field: "coding_index", sorter: "number",
            hozAlign: "right", minWidth: 55, widthGrow: 1,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? v.toFixed(1) : '<span style="color:#52525b">—</span>';
            },
        },
        {
            title: "Agent", field: "agentic_index", sorter: "number",
            hozAlign: "right", minWidth: 55, widthGrow: 1,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? v.toFixed(1) : '<span style="color:#52525b">—</span>';
            },
        },
        {
            title: "Context", field: "context_length", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? (v / 1000).toFixed(0) + 'k' : '<span style="color:#52525b">—</span>';
            },
        },
        {
            title: "Reasoning", field: "supports_reasoning", sorter: "boolean",
            hozAlign: "center", minWidth: 80, widthGrow: 1, visible: false,
            formatter: "tickCross",
        },
        {
            title: "Quant", field: "quantization", sorter: "string",
            minWidth: 60, widthGrow: 1, visible: false,
        },
        {
            title: "Uptime", field: "uptime_pct", sorter: "number",
            hozAlign: "right", minWidth: 60, widthGrow: 1, visible: false,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? v.toFixed(1) + '%' : '<span style="color:#52525b">—</span>';
            },
        },
        {
            title: "TTFT p95", field: "ttft_p95_ms", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Tok/s p95", field: "tokens_per_sec_p95", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Requests", field: "recent_requests", sorter: "number",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Benchmark", field: "benchmark_config", sorter: "string",
            minWidth: 120, widthGrow: 2, visible: false,
        },
    ];

    onMount(() => {
        table = new Tabulator(containerEl, {
            data: data,
            height: "100%",
            layout: "fitColumns",
            groupBy: "model",
            groupStartOpen: true,
            groupToggleElement: "header",
            groupHeader: (value, count) => {
                return `${value} <span style="color:#52525b;font-weight:400">${count}</span>`;
            },
            columns: COLUMNS,
            initialSort: [{ column: "ttft_ms", dir: "asc" }],
            placeholder: "No matching models",
            resizableColumnFit: true,
        });
    });

    export function replaceData(newData) {
        if (table) table.replaceData(newData);
    }

    export function getRowCount() {
        return table ? table.getDataCount() : 0;
    }
</script>

<div class="table-wrap" bind:this={containerEl}></div>

<style>
    .table-wrap {
        flex: 1;
        overflow: hidden;
    }
</style>
