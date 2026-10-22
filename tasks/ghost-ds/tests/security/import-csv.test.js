// The CSV content import route prepares asset groups from the uploaded
// archive and stores them. Its image bytes must be held to the same rule.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');

const h = require('../helpers');
const {
    prepareImportSource,
} = require('../../../core/server/services/content-import/import/source');

describe('image storage from a CSV content archive', () => {
    let tmp;

    beforeEach(function () {
        tmp = h.tempDir();
        h.useTempContentPath(tmp);
    });

    afterEach(async function () {
        await h.restoreConfig();
        fs.rmSync(tmp, { recursive: true, force: true });
    });

    async function importAssets(files) {
        const { zipPath } = await h.buildZip(tmp, files, 'posts.csv');
        const source = await prepareImportSource({ filePath: zipPath, fileName: 'posts.zip' });

        assert.ok(source.assets, 'the archive assets were not prepared');
        await source.assets.store();
        await source.cleanup();
    }

    it('CSV archive: does not store an SVG with executable content', async function () {
        await importAssets({ 'content/images/attack.svg': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('CSV archive: does not store SVG bytes behind a raster extension', async function () {
        await importAssets({ 'content/images/attack.png': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });
});
