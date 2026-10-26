import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, bodyText, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a source that redirects to a loopback address is not followed', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer({
        redirectFrom: '/redirect',
        redirectTo: `${canary.origin}/after-redirect`,
    });
    const store = new BasemapStore();

    store.add({
        protocol: 'zxy',
        url: `${tiles.origin}/tiles/{z}/{x}/{y}.png`,
        tilejson: `${tiles.origin}/redirect`,
    });

    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);
    const res = await call(handlers, 'GET', '/basemap/:basemapid/tiles', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(canary.hits, 0, `the redirect target was contacted: ${canary.paths.join(', ')}`);
    assert.ok(!bodyText(res).includes(canary.marker), 'the internal response was returned to the caller');
    assert.notEqual(res.code, 200, `a source that redirects to an internal address was reported as success`);

    await canary.close();
    await tiles.close();
});
