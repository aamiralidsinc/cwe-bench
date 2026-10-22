// A mentioned page's icon is cached into image storage. The bytes come from
// the publisher, so they must be an allowed image and SVGs must be sanitized.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const sinon = require('sinon');

const h = require('../helpers');
const OEmbedService = require('../../../core/server/services/oembed/oembed-service');
const config = require('../../../core/shared/config');
const adapterManager = require('../../../core/server/services/adapter-manager').default;

describe('mention icon storage', () => {
    let tmp;

    beforeEach(function () {
        tmp = h.tempDir();
        h.useTempContentPath(tmp);
    });

    afterEach(async function () {
        sinon.restore();
        await h.restoreConfig();
        fs.rmSync(tmp, { recursive: true, force: true });
    });

    function buildService(bytes, contentType) {
        const externalRequest = () => ({
            buffer: async () => bytes,
            headers: { 'content-type': contentType },
        });
        externalRequest.head = sinon.stub().resolves({});

        return new OEmbedService({
            config,
            externalRequest,
            imageStore: adapterManager.getAdapter('storage:images'),
        });
    }

    it('mention icon: does not store an executable SVG icon', async function () {
        const service = buildService(h.unsafeSvg(), 'image/svg+xml');

        await service.buildBookmarkData(
            'https://publisher.example/page',
            { title: 'A page', icon: 'https://publisher.example/icon' },
            'mention',
        );

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('mention icon: does not store non-image bytes served as an icon', async function () {
        const service = buildService(h.textPayload(), 'image/png');

        await service.buildBookmarkData(
            'https://publisher.example/page',
            { title: 'A page', icon: 'https://publisher.example/icon.png' },
            'mention',
        );

        assert.deepEqual(h.storageLeaks(tmp), []);
    });

    it('mention icon: does not store an unaccepted image format', async function () {
        const sharp = require('sharp');
        const avif = await sharp({
            create: { width: 8, height: 8, channels: 3, background: 'red' },
        })
            .avif()
            .toBuffer();
        const service = buildService(avif, 'image/jpeg');

        const bookmark = await service.buildBookmarkData(
            'https://publisher.example/page',
            { title: 'A page', icon: 'https://publisher.example/icon.jpg' },
            'mention',
        );

        assert.deepEqual(h.storedImageNames(tmp), [], 'an unaccepted image format was cached');
        assert.equal(bookmark.metadata.icon, 'https://publisher.example/icon.jpg');
    });
});
