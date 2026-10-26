import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a basemap source can still be updated to an ordinary public URL', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();
    store.add({ url: 'https://old.example.com/{z}/{x}/{y}.png' });
    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);

    const res = await call(handlers, 'PATCH', '/basemap/:basemapid', makeRequest({
        params: { basemapid: '1' },
        body: { url: 'https://new.example.com/{z}/{x}/{y}.png' },
    }));

    assert.equal(res.code, 200, `update was refused: ${JSON.stringify(res.body)}`);
    assert.equal(store.rows.get(1)!.url, 'https://new.example.com/{z}/{x}/{y}.png');

    await canary.close();
    await tiles.close();
});
