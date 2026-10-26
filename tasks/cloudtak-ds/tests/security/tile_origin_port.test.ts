import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, isClientError, bodyText, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a source on the configured host name but a different port is not contacted', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();

    store.add({
        protocol: 'zxy',
        url: `${tiles.origin}/tiles/{z}/{x}/{y}.png`,
        tilejson: `http://tiles.internal.test:${canary.port}/secret.json`,
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
