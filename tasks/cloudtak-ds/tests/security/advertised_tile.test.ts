import test from 'node:test';
import assert from 'node:assert';
import {
    BasemapStore, call, bodyText, loadRoutes, makeConfig, makeRequest,
    setUser, startCanary, startTileServer,
} from '../helpers.js';

test('a tile template advertised by a fetched source is not contacted', async () => {
    setUser();
    const canary = await startCanary();
    const tiles = await startTileServer({
        tilejson: {
            tilejson: '3.0.0',
            name: 'CONFIGURED-TILEJSON',
            tiles: [`${canary.origin}/tiles/{z}/{x}/{y}.png`],
        },
    });
    const store = new BasemapStore();

    store.add({
        protocol: 'zxy',
        url: `${tiles.origin}/tiles/{z}/{x}/{y}.png`,
        tilejson: `${tiles.origin}/tilejson.json`,
    });

    const config = makeConfig(store, tiles);
    const handlers = await loadRoutes(config);
    const res = await call(handlers, 'GET', '/basemap/:basemapid/tiles', makeRequest({
        params: { basemapid: '1' },
    }));

    assert.equal(canary.hits, 0, `the advertised destination was contacted: ${canary.paths.join(', ')}`);
    assert.ok(!bodyText(res).includes(canary.marker), 'the internal response was returned to the caller');

    await canary.close();
    await tiles.close();
});
