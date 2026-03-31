<script>
    import { onMount } from 'svelte';
    import 'tabulator-tables/dist/css/tabulator.min.css';
    import { TabulatorFull as Tabulator } from 'tabulator-tables';

    let { data = [] } = $props();

    let containerEl;
    let table = null;
    let resizeObserver;
    let headerTooltipEl;

    const METRIC_FIELDS = [
        'intelligence_index',
        'coding_index',
        'agentic_index',
        'ttft_ms',
        'tokens_per_sec',
        'input_price_per_m',
        'output_price_per_m',
    ];

    const ensureHeaderTooltip = () => {
        if (headerTooltipEl) return headerTooltipEl;
        headerTooltipEl = document.createElement('div');
        headerTooltipEl.className = 'table-header-tooltip';
        headerTooltipEl.setAttribute('aria-hidden', 'true');
        document.body.appendChild(headerTooltipEl);
        return headerTooltipEl;
    };

    const hideHeaderTooltip = () => {
        if (!headerTooltipEl) return;
        headerTooltipEl.classList.remove('visible');
        headerTooltipEl.setAttribute('aria-hidden', 'true');
    };

    const moveHeaderTooltip = (event) => {
        if (!headerTooltipEl || !headerTooltipEl.classList.contains('visible')) return;
        headerTooltipEl.style.left = `${event.clientX + 12}px`;
        headerTooltipEl.style.top = `${event.clientY + 12}px`;
    };

    const showHeaderTooltip = (text, event) => {
        const el = ensureHeaderTooltip();
        el.textContent = text;
        el.classList.add('visible');
        el.setAttribute('aria-hidden', 'false');
        moveHeaderTooltip(event);
    };

    const applyColumnWidths = () => {
        if (!table || !containerEl) return;

        const totalWidth = containerEl.clientWidth;
        if (!totalWidth) return;

        const isMobile = totalWidth <= 640;
        const minProviderWidth = isMobile ? 96 : 100;
        const minMetricWidth = isMobile ? 56 : 72;

        let metricWidth = Math.max(
            minMetricWidth,
            Math.ceil((totalWidth - Math.floor(totalWidth / 3)) / METRIC_FIELDS.length)
        );
        let providerWidth = isMobile
            ? Math.max(minProviderWidth, Math.floor(totalWidth * 0.42))
            : totalWidth - metricWidth * METRIC_FIELDS.length;

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

    const wireHeaderTooltips = () => {
        if (!table) return;
        for (const column of table.getColumns()) {
            const text = column.getDefinition().headerHelp;
            const el = column.getElement();
            if (!el) continue;

            el.removeAttribute('title');
            el.onmouseenter = null;
            el.onmousemove = null;
            el.onmouseleave = null;

            if (typeof text === 'string' && text) {
                el.onmouseenter = (event) => showHeaderTooltip(text, event);
                el.onmousemove = moveHeaderTooltip;
                el.onmouseleave = hideHeaderTooltip;
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
            headerHelp: "Provider or provider region for this endpoint",
            headerFilter: "input", headerFilterPlaceholder: "filter...",
            frozen: true,
            minWidth: 100,
        },
        {
            title: "Intel", field: "intelligence_index", sorter: "number",
            headerHelp: "Artificial Analysis intelligence index for the model",
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
            headerHelp: "Artificial Analysis coding index for the model",
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
            headerHelp: "Artificial Analysis agentic index for the model",
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
            headerHelp: "Time to first token in milliseconds; missing values sort last",
            sorterParams: { alignEmptyValues: "bottom" },
            hozAlign: "right", minWidth: 72,
            formatter: num,
        },
        {
            title: "Tok/s", field: "tokens_per_sec", sorter: "number",
            headerHelp: "Median output throughput in tokens per second; missing values sort last",
            sorterParams: { alignEmptyValues: "bottom" },
            hozAlign: "right", minWidth: 72,
            formatter: num,
        },
        {
            title: "$/M in", field: "input_price_per_m", sorter: "number",
            headerHelp: "Input token price in USD per 1 million tokens",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '<span style="color:var(--text-dim)">—</span>';
                return v < 0.01 ? '<span style="color:var(--green)">Free</span>' : '$' + v.toFixed(2);
            },
        },
        {
            title: "$/M out", field: "output_price_per_m", sorter: "number",
            headerHelp: "Output token price in USD per 1 million tokens",
            hozAlign: "right", minWidth: 72,
            formatter: (cell) => {
                const v = cell.getValue();
                if (v == null) return '<span style="color:var(--text-dim)">—</span>';
                return v < 0.01 ? '<span style="color:var(--green)">Free</span>' : '$' + v.toFixed(2);
            },
        },

        {
            title: "Context", field: "context_length", sorter: "number",
            headerHelp: "Maximum context window length",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? (v / 1000).toFixed(0) + 'k' : '<span style="color:var(--text-dim)">—</span>';
            },
        },
        {
            title: "Reasoning", field: "supports_reasoning", sorter: "boolean",
            headerHelp: "Whether the endpoint supports reasoning mode",
            hozAlign: "center", minWidth: 80, widthGrow: 1, visible: false,
            formatter: "tickCross",
        },
        {
            title: "Quant", field: "quantization", sorter: "string",
            headerHelp: "Model quantization or precision label",
            minWidth: 60, widthGrow: 1, visible: false,
        },
        {
            title: "Uptime", field: "uptime_pct", sorter: "number",
            headerHelp: "Provider uptime percentage over the last 30 minutes",
            hozAlign: "right", minWidth: 60, widthGrow: 1, visible: false,
            formatter: (cell) => {
                const v = cell.getValue();
                return v != null ? v.toFixed(1) + '%' : '<span style="color:var(--text-dim)">—</span>';
            },
        },
        {
            title: "TTFT p95", field: "ttft_p95_ms", sorter: "number",
            headerHelp: "95th percentile time to first token in milliseconds",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Tok/s p95", field: "tokens_per_sec_p95", sorter: "number",
            headerHelp: "95th percentile output throughput in tokens per second",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Requests", field: "recent_requests", sorter: "number",
            headerHelp: "Recent request volume in the stats window",
            hozAlign: "right", minWidth: 70, widthGrow: 1, visible: false,
            formatter: num,
        },
        {
            title: "Benchmark", field: "benchmark_config", sorter: "string",
            headerHelp: "Artificial Analysis benchmark configuration used for model scores",
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
            applyColumnWidths();
            wireHeaderTooltips();
        };

        table.on("renderComplete", syncHeaderAndWidths);
        applyColumnWidths();

        resizeObserver = new ResizeObserver(() => {
            applyColumnWidths();
        });
        resizeObserver.observe(containerEl);

        return () => {
            resizeObserver?.disconnect();
            resizeObserver = null;
            hideHeaderTooltip();
            headerTooltipEl?.remove();
            headerTooltipEl = null;
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
