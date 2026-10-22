// The CSV content import route keeps storing real image, avatar, media and
// file assets.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const h = require('../helpers');
const {
    prepareImportSource,
} = require('../../../core/server/services/content-import/import/source');

describe('CSV content archive import', () => {
    let tmp;

    beforeEach(function () {
        tmp = h.tempDir();
        h.useTempContentPath(tmp);
    });

    afterEach(async function () {
        await h.restoreConfig();
        fs.rmSync(tmp, { recursive: true, force: true });
    });

    it('CSV archive: stores image, avatar, media and file assets', async function () {
        const movie = Buffer.from('CWE_GHOST_DS_MEDIA');
        const guide = Buffer.from('CWE_GHOST_DS_FILE');
        const { zipPath } = await h.buildZip(
            tmp,
            {
                'content/images/photo.jpg': h.fixture('ghosticon.jpg'),
                'content/avatars/me.png': h.fixture('ghost-logo.png'),
                'content/media/movie.mp4': movie,
                'content/files/guide.pdf': guide,
            },
            'posts.csv',
        );

        const source = await prepareImportSource({ filePath: zipPath, fileName: 'posts.zip' });
        assert.ok(source.assets, 'the archive assets were not prepared');
        await source.assets.store();
        await source.cleanup();

        const content = path.join(tmp, 'content');
        const images = h.storedIn(content, 'images').map((file) => path.basename(file));
        assert.ok(images.includes('photo.jpg'), 'the image was not stored');
        assert.ok(images.includes('me.png'), 'the avatar was not stored');

        const media = h.storedIn(content, 'media');
        assert.equal(media.length, 1);
        assert.deepEqual(fs.readFileSync(media[0]), movie);

        const files = h.storedIn(content, 'files');
        assert.equal(files.length, 1);
        assert.deepEqual(fs.readFileSync(files[0]), guide);
    });
});
