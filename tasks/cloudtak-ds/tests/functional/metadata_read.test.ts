import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('basemap details are still returned', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();
    store.add({ name: 'details-basemap', url: 'https://tiles.example.com/{z}/{x}/{y}.png' });
    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);

    const res = await call(handlers, 'GET', '/basemap/:basemapid', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(res.code, 200, `details were refused: ${JSON.stringify(res.body)}`);
    assert.equal(res.body.name, 'details-basemap');
    assert.ok(res.body.actions && Array.isArray(res.body.actions.feature));

    await canary.close();
    await tiles.close();
});
