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

    // Fetch the .duckdb file and register it
    const response = await fetch(dbUrl);
    const buffer = new Uint8Array(await response.arrayBuffer());
    await db.registerFileBuffer('openrouter.duckdb', buffer);

    // Open a default in-memory database (not the file)
    await db.open({});
    conn = await db.connect();

    // Attach the file read-only, then copy all tables into the in-memory default DB
    await conn.query(`ATTACH 'openrouter.duckdb' AS src (READ_ONLY)`);
    const tables = await conn.query(`SELECT table_name FROM information_schema.tables WHERE table_catalog = 'src'`);
    for (const row of tables.toArray()) {
        const name = row.toJSON().table_name;
        await conn.query(`CREATE TABLE ${name} AS SELECT * FROM src.${name}`);
    }
    await conn.query(`DETACH src`);

    return conn;
}

export async function query(sql) {
    if (!conn) throw new Error('Database not initialized');
    const result = await conn.query(sql);
    // Convert BigInt values to Number (DuckDB-WASM returns BigInt for int64)
    return result.toArray().map(row => {
        const obj = row.toJSON();
        for (const key in obj) {
            if (typeof obj[key] === 'bigint') {
                obj[key] = Number(obj[key]);
            }
        }
        return obj;
    });
}
