// A file offered as an image is also picked up by the archive's ordinary
// content-file handlers. When its contents do not qualify it must not be
// written to any storage, not just the image store.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');

const h = require('../helpers');
const ImportManager = require('../../../core/server/data/importer/import-manager');
const {
    createContentFileImporters,
} = require('../../../core/server/data/importer/content-files');

// Store every content-file group the archive prepared, the way the importer does.
const storeAll = async (importData) => {
    for (const importer of createContentFileImporters()) {
        const files = importData[importer.type] || [];
        if (files.length) {
            await importer.doImport(files);
        }
    }
};

describe('archive image bytes across storage', () => {
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

    async function importEverything(files) {
        const { zipPath } = await h.buildZip(tmp, files, null);
        const importData = await ImportManager.loadFile({ name: 'import.zip', path: zipPath });
        await storeAll(importData);
        return importData;
    }

    it('archive import: keeps unusable image bytes out of every storage', async function () {
        await importEverything({ 'content/images/attack.jpg': h.textPayload() });

        assert.deepEqual(h.contentLeaks(tmp), []);
    });

    it('archive import: keeps disguised vector bytes out of every storage', async function () {
        await importEverything({ 'content/images/attack.png': h.unsafeSvg() });

        assert.deepEqual(h.contentLeaks(tmp), []);
    });
});
