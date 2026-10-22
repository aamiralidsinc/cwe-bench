// Avatar assets carried by a CSV content archive are stored as images too.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');

const h = require('../helpers');
const {
    prepareImportSource,
} = require('../../../core/server/services/content-import/import/source');

describe('avatar storage from a CSV content archive', () => {
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

    it('CSV avatar archive: does not store an executable SVG', async function () {
        await importAssets({ 'content/avatars/attack.svg': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('CSV avatar archive: does not store SVG behind a raster name', async function () {
        await importAssets({ 'content/avatars/attack.png': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('CSV avatar archive: does not store non-image bytes behind a raster name', async function () {
        await importAssets({ 'content/avatars/attack.png': h.textPayload() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('CSV avatar archive: does not store an unaccepted image format', async function () {
        const sharp = require('sharp');
        const avif = await sharp({
            create: { width: 8, height: 8, channels: 3, background: 'red' },
        })
            .avif()
            .toBuffer();

        await importAssets({ 'content/avatars/avif-attack.png': avif });

        assert.equal(
            h.storedImageNames(tmp).some((name) => name.includes('avif-attack')),
            false,
            'AVIF bytes named as an accepted avatar are stored',
        );
    });
});
