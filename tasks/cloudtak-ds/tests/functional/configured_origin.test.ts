import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('the operator-configured tile origin still serves TileJSON', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer();
    const store = new BasemapStore();

    store.add({
        protocol: 'zxy',
        url: `${tiles.origin}/tiles/{z}/{x}/{y}.png`,
        tilejson: `${tiles.origin}/nested/path/tilejson.json`,
    });

    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);
    const res = await call(handlers, 'GET', '/basemap/:basemapid/tiles', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(res.code, 200, `configured origin was refused: ${JSON.stringify(res.body)}`);
    assert.equal(res.body.name, 'CONFIGURED-TILEJSON');
    const requested = tiles.requests.join(' ');
    assert.match(requested, /\/nested\/path\/tilejson\.json/, 'the configured path was not requested');
    assert.match(requested, /token=test-token/, 'the access token was not forwarded to the configured origin');
    assert.equal(canary.hits, 0);

    await canary.close();
    await tiles.close();
});
