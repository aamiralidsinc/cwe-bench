// Remote media fetched by the inliner is written to the storage its extension
// picks. Image storage must only receive real allowed images, and SVG bytes
// must be sanitized before they are stored.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const sinon = require('sinon');

const h = require('../helpers');
const mediaInlinerService = require('../../../core/server/services/media-inliner');

describe('remote media image storage', () => {
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

    const response = (body, contentType) => ({
        body,
        headers: { 'content-type': contentType },
    });

    it('remote media: does not store an executable SVG response', async function () {
        sinon
            .stub(inliner, 'getRemoteMedia')
            .resolves(response(h.unsafeSvg(), 'image/svg+xml'));

        await inliner.importUrl('https://media.example/attack.svg');

        assert.deepEqual(h.storageLeaks(tmp), []);
        assert.deepEqual(h.contentLeaks(tmp), [], 'the rejected bytes were stored outside image storage');
    });

    it('remote media: does not store SVG served as a raster image', async function () {
        sinon.stub(inliner, 'getRemoteMedia').resolves(response(h.unsafeSvg(), 'image/png'));

        const result = await inliner.importUrl('https://media.example/attack.png');

        assert.notEqual(result.status, 'stored');
        assert.deepEqual(h.storageLeaks(tmp), []);
        assert.deepEqual(h.contentLeaks(tmp), [], 'the rejected bytes were stored outside image storage');
    });

    it('remote media: does not store non-image bytes served as an image', async function () {
        sinon.stub(inliner, 'getRemoteMedia').resolves(response(h.textPayload(), 'image/jpeg'));

        const result = await inliner.importUrl('https://media.example/attack.jpg');

        assert.notEqual(result.status, 'stored');
        assert.deepEqual(h.storageLeaks(tmp), []);
        assert.deepEqual(h.contentLeaks(tmp), [], 'the rejected bytes were stored outside image storage');
    });

    it('remote media: a skipped file does not stop the next one', async function () {
        sinon
            .stub(inliner, 'getRemoteMedia')
            .callsFake(async (url) =>
                url.includes('bad.example')
                    ? response(h.unsafeSvg(), 'image/png')
                    : response(h.fixture('ghosticon.jpg'), 'image/jpeg'),
            );

        const content = JSON.stringify({
            children: [
                { src: 'https://bad.example/attack.png' },
                { src: 'https://media.example/good.jpg' },
            ],
        });

        const updated = await inliner.inlineContent(content, ['https?://(?:bad|media)\\.example']);

        assert.ok(updated.includes('https://bad.example/attack.png'), 'the bad file was treated as stored');
        assert.equal(updated.includes('https://media.example/good.jpg'), false, 'the later file was skipped');
        assert.deepEqual(h.contentLeaks(tmp), []);
        assert.equal(h.storedIn(path.join(tmp, 'content'), 'images').length, 1);
    });
});
