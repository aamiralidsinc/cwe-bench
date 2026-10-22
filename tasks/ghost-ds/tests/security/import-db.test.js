// Image bytes carried by a content archive must not reach image storage unless
// they are an allowed image; SVG content must be sanitized first.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const h = require('../helpers');
const ImportManager = require('../../../core/server/data/importer/import-manager');
const {
    createContentFileImporters,
} = require('../../../core/server/data/importer/content-files');

const storeImages = async (importData) => {
    const images = createContentFileImporters().find((importer) => importer.type === 'images');
    return images.doImport(importData.images || []);
};

describe('image storage from a content archive', () => {
    let tmp;

    beforeEach(function () {
        tmp = h.tempDir();
        h.useTempContentPath(tmp);
    });

    afterEach(async function () {
        await ImportManager.cleanUp();
        await h.restoreConfig();
        fs.rmSync(tmp, { recursive: true, force: true });
    });

    async function importAndStore(files) {
        const { zipPath } = await h.buildZip(tmp, files);
        const importData = await ImportManager.loadFile({ name: 'import.zip', path: zipPath });
        await storeImages(importData);
    }

    it('archive import: does not store an SVG with executable content', async function () {
        await importAndStore({ 'content/images/attack.svg': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('archive import: does not store a gzipped SVG with executable content', async function () {
        await importAndStore({ 'content/images/attack.svgz': h.unsafeSvgz() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('archive import: does not store an SVG with an upper-case extension', async function () {
        await importAndStore({ 'content/images/attack.SVG': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('archive import: does not store SVG bytes behind a raster extension', async function () {
        await importAndStore({ 'content/images/attack.png': h.unsafeSvg() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('archive import: does not store non-image bytes behind a raster extension', async function () {
        await importAndStore({ 'content/images/attack.jpg': h.textPayload() });

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('archive import: does not store an unaccepted image format', async function () {
        const sharp = require('sharp');
        const avif = await sharp({
            create: { width: 8, height: 8, channels: 3, background: 'red' },
        })
            .avif()
            .toBuffer();

        await importAndStore({ 'content/images/avif-attack.jpg': avif });

        assert.equal(
            h.storedImageNames(tmp).some((name) => name.includes('avif-attack')),
            false,
            'AVIF bytes named as an accepted image are stored',
        );
    });
});
