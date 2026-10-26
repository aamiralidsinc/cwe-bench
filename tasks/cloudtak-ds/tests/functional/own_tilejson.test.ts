import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a basemap that carries its own TileJSON still reports it without contacting anything', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();
    store.add({
        name: 'local-basemap',
        protocol: 'zxy',
        url: 'https://tiles.example.com/{z}/{x}/{y}.png',
        tilejson: 'local-metadata',
    });
    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);

    const res = await call(handlers, 'GET', '/basemap/:basemapid/tiles', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(res.code, 200, `metadata was refused: ${JSON.stringify(res.body)}`);
    assert.equal(res.body.name, 'local-basemap');
    assert.equal(canary.hits, 0);
    assert.equal(tiles.requests.length, 0);

    await canary.close();
    await tiles.close();
});
