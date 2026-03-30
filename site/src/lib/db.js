import * as duckdb from '@duckdb/duckdb-wasm';

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

    const response = await fetch(dbUrl, { cache: 'no-cache' });
    const buffer = new Uint8Array(await response.arrayBuffer());
    await db.registerFileBuffer('openrouter.duckdb', buffer);

    await db.open({});
    conn = await db.connect();

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
