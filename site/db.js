import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.30.0/+esm';

let db = null;
let conn = null;

export async function initDB(dbUrl) {
    const BUNDLES = duckdb.getJsDelivrBundles();
    const bundle = await duckdb.selectBundle(BUNDLES);

    const workerUrl = URL.createObjectURL(
        new Blob([`importScripts("${bundle.mainWorker}");`], { type: 'text/javascript' })
    );

    const worker = new Worker(workerUrl);
    const logger = new duckdb.ConsoleLogger();
    db = new duckdb.AsyncDuckDB(logger, worker);
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    URL.revokeObjectURL(workerUrl);

    const response = await fetch(dbUrl);
    const buffer = new Uint8Array(await response.arrayBuffer());
    await db.registerFileBuffer('openrouter.duckdb', buffer);
    await db.open({ path: 'openrouter.duckdb' });

    conn = await db.connect();
    return conn;
}

export async function query(sql) {
    if (!conn) throw new Error('Database not initialized');
    const result = await conn.query(sql);
    return result.toArray().map(row => row.toJSON());
}
