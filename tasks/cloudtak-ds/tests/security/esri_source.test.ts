import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, isClientError, bodyText, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a stored ESRI-layer source is not contacted when it resolves to loopback', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();

    store.add({
        protocol: 'FeatureServer',
        type: 'vector',
        url: `${canary.origin}/arcgis/rest/services/internal/FeatureServer/0`,
    });

    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);
    const res = await call(handlers, 'GET', '/basemap/:basemapid/tiles', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(canary.hits, 0, `the internal service was contacted: ${canary.paths.join(', ')}`);
    assert.ok(isClientError(res), `expected a client error, got ${res.code}`);
    assert.ok(!bodyText(res).includes(canary.marker), 'the internal response was returned to the caller');

    await canary.close();
    await tiles.close();
});
