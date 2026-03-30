<script>
    import { onMount } from 'svelte';
    import 'tabulator-tables/dist/css/tabulator.min.css';
    import { TabulatorFull as Tabulator } from 'tabulator-tables';

    let { data = [] } = $props();

    let containerEl;
    let table = null;
    let resizeObserver;

    const METRIC_FIELDS = [
        'intelligence_index',
        'coding_index',
        'agentic_index',
        'ttft_ms',
        'tokens_per_sec',
        'input_price_per_m',
        'output_price_per_m',
    ];

    const applyColumnWidths = () => {
        if (!table || !containerEl) return;

        const totalWidth = containerEl.clientWidth;
        if (!totalWidth) return;

        const minProviderWidth = 100;
        const minMetricWidth = 72;

        let metricWidth = Math.max(
            minMetricWidth,
            Math.ceil((totalWidth - Math.floor(totalWidth / 3)) / METRIC_FIELDS.length)
        );
        let providerWidth = totalWidth - metricWidth * METRIC_FIELDS.length;

        if (providerWidth < minProviderWidth) {
            providerWidth = minProviderWidth;
            metricWidth = Math.floor((totalWidth - providerWidth) / METRIC_FIELDS.length);
        }

        const columnsByField = Object.fromEntries(
            table.getColumns().map((column) => [column.getField(), column])
        );

        columnsByField.provider?.setWidth(providerWidth);
        for (const field of METRIC_FIELDS) {
            columnsByField[field]?.setWidth(metricWidth);
        }
    };

    const applyHeaderTooltips = () => {
        if (!table) return;
        for (const column of table.getColumns()) {
            const tooltip = column.getDefinition().headerTooltip;
            if (typeof tooltip === 'string' && tooltip) {
                column.getElement()?.setAttribute('title', tooltip);
            }
        }
    };

    const num = (cell) => {
        const v = cell.getValue();
        return v != null ? Math.round(v).toLocaleString() : '<span style="color:var(--text-dim)">—</span>';
    };

    const COLUMNS = [
        {
            title: "Provider", field: "provider", sorter: "string",
            headerTooltip: "Provider or provider region for this endpoint",
            headerFilter: "input", headerFilterPlaceholder: "filter...",
            minWidth: 100,
        },
        {
            title: "Intel", field: "intelligence_index", sorter: "number",
            headerTooltip: "Artificial Analysis intelligence index for the model",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '';
                const row = cell.getRow();
                const group = row.getGroup();
                const rows = group ? group.getRows() : [];
                if (rows.length > 0 && rows[0] !== row) return '';
                return `<span style="color:var(--benchmark-intel)">${v.toFixed(1)}</span>`;
            },
        },
        {
            title: "Code", field: "coding_index", sorter: "number",
            headerTooltip: "Artificial Analysis coding index for the model",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '';
                const row = cell.getRow();
                const group = row.getGroup();
                const rows = group ? group.getRows() : [];
                if (rows.length > 0 && rows[0] !== row) return '';
                return `<span style="color:var(--benchmark-code)">${v.toFixed(1)}</span>`;
            },
        },
        {
            title: "Agent", field: "agentic_index", sorter: "number",
            headerTooltip: "Artificial Analysis agentic index for the model",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '';
                const row = cell.getRow();
                const group = row.getGroup();
                const rows = group ? group.getRows() : [];
                if (rows.length > 0 && rows[0] !== row) return '';
                return `<span style="color:var(--benchmark-agent)">${v.toFixed(1)}</span>`;
            },
        },
        {
            title: "TTFT", field: "ttft_ms", sorter: "number",
            headerTooltip: "Time to first token in milliseconds; missing values sort last",
            sorterParams: { alignEmptyValues: "bottom" },
            hozAlign: "right", minWidth: 72,
            formatter: num,
        },
        {
            title: "Tok/s", field: "tokens_per_sec", sorter: "number",
            headerTooltip: "Median output throughput in tokens per second; missing values sort last",
            sorterParams: { alignEmptyValues: "bottom" },
            hozAlign: "right", minWidth: 72,
            formatter: num,
        },
        {
            title: "$/M in", field: "input_price_per_m", sorter: "number",
            headerTooltip: "Input token price in USD per 1 million tokens",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '<span style="color:var(--text-dim)">—</span>';
                return v < 0.01 ? '<span style="color:var(--green)">Free</span>' : '$' + v.toFixed(2);
            },
        },
        {
            title: "$/M out", field: "output_price_per_m", sorter: "number",
            headerTooltip: "Output token price in USD per 1 million tokens",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '<span style="color:var(--text-dim)">—</span>';
                return v < 0.01 ? '<span style="color:var(--green)">Free</span>' : '$' + v.toFixed(2);
            },
        },

        {
            title: "Context", field: "context_length", sorter: "number",
            headerTooltip: "Maximum context window length",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? (v / 1000).toFixed(0) + 'k' : '<span style="color:var(--text-dim)">—</span>';
            },
        },
        {
            title: "Reasoning", field: "supports_reasoning", sorter: "boolean",
            headerTooltip: "Whether the endpoint supports reasoning mode",
            hozAlign: "center", minWidth: 80, widthGrow: 1, visible: false,
            formatter: "tickCross",
        },
        {
            title: "Quant", field: "quantization", sorter: "string",
            headerTooltip: "Model quantization or precision label",
            minWidth: 60, widthGrow: 1, visible: false,
        },
        {
            title: "Uptime", field: "uptime_pct", sorter: "number",
            headerTooltip: "Provider uptime percentage over the last 30 minutes",
            hozAlign: "right", minWidth: 60, widthGrow: 1, visible: false,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? v.toFixed(1) + '%' : '<span style="color:var(--text-dim)">—</span>';
            },
        },
        {
            title: "TTFT p95", field: "ttft_p95_ms", sorter: "number",
            headerTooltip: "95th percentile time to first token in milliseconds",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Tok/s p95", field: "tokens_per_sec_p95", sorter: "number",
            headerTooltip: "95th percentile output throughput in tokens per second",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Requests", field: "recent_requests", sorter: "number",
            headerTooltip: "Recent request volume in the stats window",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Benchmark", field: "benchmark_config", sorter: "string",
            headerTooltip: "Artificial Analysis benchmark configuration used for model scores",
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
                return `${value} <span style="color:var(--text-dim);font-weight:400">${count}</span>`;
            },
            columns: COLUMNS,
            initialSort: [{ column: "ttft_ms", dir: "asc" }],
            placeholder: "No matching models",
            resizableColumnFit: true,
        });

        const syncHeaderAndWidths = () => {
            applyHeaderTooltips();
            applyColumnWidths();
        };

        table.on("renderComplete", syncHeaderAndWidths);
        applyHeaderTooltips();
        applyColumnWidths();

        resizeObserver = new ResizeObserver(() => {
            applyColumnWidths();
        });
        resizeObserver.observe(containerEl);

        return () => {
            resizeObserver?.disconnect();
            resizeObserver = null;
            table?.destroy();
            table = null;
        };
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
