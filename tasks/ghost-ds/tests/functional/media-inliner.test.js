// The inliner keeps storing real images, SVGs, media and files into the
// storage their extension picks.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const sinon = require('sinon');

const h = require('../helpers');
const mediaInlinerService = require('../../../core/server/services/media-inliner');

describe('remote media inlining', () => {
    let tmp;
    let inliner;

    beforeEach(async function () {
        tmp = h.tempDir();
        h.useTempContentPath(tmp);
        await mediaInlinerService.init();
        inliner = mediaInlinerService.getInstance();
    });

    afterEach(async function () {
        sinon.restore();
        await h.restoreConfig();
        fs.rmSync(tmp, { recursive: true, force: true });
    });

    const respond = (body, contentType) => ({
        body,
        headers: { 'content-type': contentType },
    });

    it('remote media: stores a real remote image', async function () {
        sinon
            .stub(inliner, 'getRemoteMedia')
            .resolves(respond(h.fixture('ghosticon.jpg'), 'image/jpeg'));

        const result = await inliner.importUrl('https://media.example/photo.jpg');

        assert.equal(result.status, 'stored');
        assert.equal(h.storedIn(path.join(tmp, 'content'), 'images').length, 1);
        const [stored] = h.storedIn(path.join(tmp, 'content'), 'images');
        assert.deepEqual(fs.readFileSync(stored), h.fixture('ghosticon.jpg'));
    });

    it('remote media: still stores a remote SVG', async function () {
        sinon
            .stub(inliner, 'getRemoteMedia')
            .resolves(respond(h.unsafeSvg(), 'image/svg+xml'));

        const result = await inliner.importUrl('https://media.example/logo.svg');

        assert.equal(result.status, 'stored');
        const stored = h.storedIn(path.join(tmp, 'content'), 'images');
        assert.equal(stored.length, 1);
        assert.ok(h.readMaybeZipped(stored[0]).toString().includes('<svg'));
    });

    it('remote media: an unaccepted image format is not stored as an image', async function () {
        const sharp = require('sharp');
        const avif = await sharp({
            create: { width: 8, height: 8, channels: 3, background: 'red' },
        })
            .avif()
            .toBuffer();

        sinon.stub(inliner, 'getRemoteMedia').resolves(respond(avif, 'image/jpeg'));

        await inliner.importUrl('https://media.example/photo.jpg');

        assert.deepEqual(
            h.storedIn(path.join(tmp, 'content'), 'images'),
            [],
            'an image format the site does not accept was stored as an image',
        );
    });

    it('remote media: routes media and file responses to their own storage', async function () {
        sinon
            .stub(inliner, 'getRemoteMedia')
            .resolves(respond(Buffer.from('CWE_GHOST_DS_MEDIA'), 'video/mp4'));
        const media = await inliner.importUrl('https://media.example/movie.mp4');
        assert.equal(media.status, 'stored');

        sinon.restore();
        await mediaInlinerService.init();
        inliner = mediaInlinerService.getInstance();
        sinon
            .stub(inliner, 'getRemoteMedia')
            .resolves(respond(Buffer.from('CWE_GHOST_DS_FILE'), 'application/pdf'));
        const file = await inliner.importUrl('https://media.example/guide.pdf');
        assert.equal(file.status, 'stored');

        assert.equal(h.storedIn(path.join(tmp, 'content'), 'media').length, 1);
        assert.equal(h.storedIn(path.join(tmp, 'content'), 'files').length, 1);
    });
});
