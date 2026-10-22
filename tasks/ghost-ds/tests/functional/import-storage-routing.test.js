// Legitimate archives still route every asset kind to its own storage, and an
// image attached as a download keeps working next to the image assets.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const h = require('../helpers');
const ImportManager = require('../../../core/server/data/importer/import-manager');
const {
    createContentFileImporters,
} = require('../../../core/server/data/importer/content-files');

const storeAll = async (importData) => {
    for (const importer of createContentFileImporters()) {
        const files = importData[importer.type] || [];
        if (files.length) {
            await importer.doImport(files);
        }
    }
};

describe('archive storage routing', () => {
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

    it('archive import: stores an image asset and an image download in their own storage', async function () {
        const photo = h.fixture('ghosticon.jpg');
        const guide = Buffer.from('%PDF-1.4\nCWE_GHOST_DS_FILE');
        const movie = Buffer.from('CWE_GHOST_DS_MEDIA');

        const { zipPath } = await h.buildZip(
            tmp,
            {
                'content/images/photo.jpg': photo,
                'content/files/photo.jpg': photo,
                'content/files/guide.pdf': guide,
                'content/media/movie.mp4': movie,
            },
            null,
        );

        const importData = await ImportManager.loadFile({ name: 'import.zip', path: zipPath });
        await storeAll(importData);

        const content = path.join(tmp, 'content');
        const imageNames = h.storedIn(content, 'images').map((file) => path.basename(file));
        assert.ok(imageNames.includes('photo.jpg'), 'the image asset was not stored');

        const fileNames = h.storedIn(content, 'files');
        const byName = (name) => fileNames.find((file) => path.basename(file) === name);
        assert.ok(byName('photo.jpg'), 'the image attached as a download was dropped');
        assert.ok(byName('guide.pdf'), 'the download was dropped');
        assert.deepEqual(fs.readFileSync(byName('photo.jpg')), photo);

        const mediaNames = h.storedIn(content, 'media').map((file) => path.basename(file));
        assert.ok(mediaNames.includes('movie.mp4'), 'the media file was not stored');
    });
});
