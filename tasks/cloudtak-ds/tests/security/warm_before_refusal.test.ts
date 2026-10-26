import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, isClientError, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a refused source is not contacted before the refusal', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();

    store.add({
        protocol: 'zxy',
        url: `${tiles.origin}/tiles/{z}/{x}/{y}.png`,
        tilejson: `${canary.origin}/metadata.json`,
    });

    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);
    const res = await call(handlers, 'GET', '/basemap/:basemapid/tiles', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(canary.hits, 0, `the refused source was contacted: ${canary.paths.join(', ')}`);
    assert.ok(isClientError(res), `expected a client error, got ${res.code}`);

    await canary.close();
    await tiles.close();
});
