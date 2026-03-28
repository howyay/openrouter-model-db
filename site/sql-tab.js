let resultsTable = null;

export function initSqlTab(queryFn) {
    const runBtn = document.getElementById('sql-run');
    const input = document.getElementById('sql-input');
    const errorEl = document.getElementById('sql-error');

    async function runQuery() {
        errorEl.classList.add('hidden');
        const sql = input.value.trim();
        if (!sql) return;

        try {
            const rows = await queryFn(sql);
            if (rows.length === 0) {
                errorEl.textContent = 'Query returned 0 rows.';
                errorEl.classList.remove('hidden');
                if (resultsTable) resultsTable.destroy();
                resultsTable = null;
                return;
            }

            const columns = Object.keys(rows[0]).map(key => ({
                title: key,
                field: key,
                sorter: typeof rows[0][key] === 'number' ? 'number' : 'string',
                headerFilter: "input",
            }));

            if (resultsTable) resultsTable.destroy();
            resultsTable = new Tabulator('#sql-results', {
                data: rows,
                columns: columns,
                height: "100%",
                layout: "fitDataFill",
                placeholder: "No results",
            });
        } catch (e) {
            errorEl.textContent = e.message || String(e);
            errorEl.classList.remove('hidden');
        }
    }

    runBtn.addEventListener('click', runQuery);
    input.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runQuery();
        }
    });
}
