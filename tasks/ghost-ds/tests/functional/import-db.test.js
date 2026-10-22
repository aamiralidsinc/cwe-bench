// Legitimate imports keep working: real images are stored, SVG/SVGZ are still
// accepted, one unusable file does not abort the import, and non-image asset
// kinds are untouched.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const h = require('../helpers');
const ImportManager = require('../../../core/server/data/importer/import-manager');
const {
    createContentFileImporters,
} = require('../../../core/server/data/importer/content-files');

const importerFor = (type) =>
    createContentFileImporters().find((importer) => importer.type === type);

describe('content archive import', () => {
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

    async function load(files) {
        const { zipPath } = await h.buildZip(tmp, files);
        return ImportManager.loadFile({ name: 'import.zip', path: zipPath });
    }

    it('archive import: stores every allowed image format, including alias spellings', async function () {
        const importData = await load({
            'content/images/photo.jpg': h.fixture('ghosticon.jpg'),
            'content/images/photo.jpeg': h.fixture('ghosticon.jpg'),
            'content/images/PHOTO.JPG': h.fixture('ghosticon.jpg'),
            'content/images/logo.png': h.fixture('ghost-logo.png'),
            'content/images/anim.gif': h.fixture('loadingcat.gif'),
            'content/images/pic.webp': h.fixture('ghosticon.webp'),
            'content/images/icon.ico': h.fixture('myicon.ico'),
            // contents in another allowed format than the name
            'content/images/mismatch.jpg': h.fixture('ghost-logo.png'),
        });

        assert.equal(importData.images.length, 8);
        const stored = await importerFor('images').doImport(importData.images);
        assert.equal(stored.length, 8);

        const names = h.storedImageNames(tmp).map((name) => path.basename(name));
        for (const name of [
            'photo.jpg',
            'photo.jpeg',
            'PHOTO.JPG',
            'logo.png',
            'anim.gif',
            'pic.webp',
            'icon.ico',
            'mismatch.jpg',
        ]) {
            assert.ok(names.includes(name), `${name} was not stored`);
        }
    });

    it('archive import: still imports SVG and SVGZ images', async function () {
        const importData = await load({
            'content/images/vector.svg': h.fixture('ghost-logo.svg'),
            'content/images/packed.svgz': h.fixture('ghost-logo.svgz'),
        });

        assert.equal(importData.images.length, 2);
        await importerFor('images').doImport(importData.images);

        const files = h.walk(path.join(tmp, 'content', 'images'));
        const svg = files.find((file) => file.endsWith('vector.svg'));
        const svgz = files.find((file) => file.endsWith('packed.svgz'));
        assert.ok(svg, 'the SVG was not stored');
        assert.ok(svgz, 'the SVGZ was not stored');
        assert.ok(h.readMaybeZipped(svg).toString().includes('<svg'));
        assert.ok(h.readMaybeZipped(svgz).toString().includes('<svg'));
    });

    it('archive import: keeps valid images when one file is unusable', async function () {
        const importData = await load({
            'content/images/good.jpg': h.fixture('ghosticon.jpg'),
            'content/images/not-an-image.png': h.textPayload(),
        });

        assert.ok(
            importData.images.some((file) => file.originalPath.endsWith('good.jpg')),
            'the valid image was dropped',
        );
        await importerFor('images').doImport(importData.images);

        const names = h.storedImageNames(tmp).map((name) => path.basename(name));
        assert.ok(names.includes('good.jpg'));
    });

    it('archive import: imports a non-image download attached to the archive', async function () {
        const bytes = Buffer.from('%PDF-1.4\nCWE_GHOST_DS_DOWNLOAD');
        const importData = await load({ 'content/files/guide.pdf': bytes });

        assert.equal(importData.files.length, 1);
        await importerFor('files').doImport(importData.files);

        const stored = h.storedIn(path.join(tmp, 'content'), 'files');
        assert.equal(stored.length, 1);
        assert.deepEqual(fs.readFileSync(stored[0]), bytes);
    });
});
