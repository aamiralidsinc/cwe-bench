import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a basemap with an ordinary public tile URL can still be created', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();
    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);

    const res = await call(handlers, 'POST', '/basemap', makeRequest({
        body: {
            name: 'public-basemap',
            url: 'https://tiles.example.com/{z}/{x}/{y}.png',
            protocol: 'zxy',
            type: 'raster',
            scope: 'user',
        },
    }));

    assert.equal(res.code, 200, `create was refused: ${JSON.stringify(res.body)}`);
    assert.equal(store.rows.size, 1);
    const row = [...store.rows.values()][0];
    assert.equal(row.url, 'https://tiles.example.com/{z}/{x}/{y}.png');
    assert.ok(res.body.actions && Array.isArray(res.body.actions.feature));

    await canary.close();
    await tiles.close();
});
