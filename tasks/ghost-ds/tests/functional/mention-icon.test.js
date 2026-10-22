// Caching a mention's icon keeps working for real images, and a failed fetch
// leaves the bookmark usable.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const sinon = require('sinon');

const h = require('../helpers');
const OEmbedService = require('../../../core/server/services/oembed/oembed-service');
const config = require('../../../core/shared/config');
const adapterManager = require('../../../core/server/services/adapter-manager').default;

describe('mention icon caching', () => {
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

    it('mention icon: stores a real icon and returns its local URL', async function () {
        const bytes = h.fixture('ghost-logo.png');
        const externalRequest = () => ({
            buffer: async () => bytes,
            headers: { 'content-type': 'image/png' },
        });
        externalRequest.head = sinon.stub().resolves({});

        const service = new OEmbedService({
            config,
            externalRequest,
            imageStore: adapterManager.getAdapter('storage:images'),
        });

        const bookmark = await service.buildBookmarkData(
            'https://publisher.example/page',
            { title: 'A page', icon: 'https://publisher.example/icon.png' },
            'mention',
        );

        const stored = h.storedIn(path.join(tmp, 'content'), 'images');
        assert.equal(stored.length, 1);
        assert.deepEqual(fs.readFileSync(stored[0]), bytes);
        assert.equal(bookmark.metadata.icon.startsWith('/content/images/icon/'), true);
    });

    it('mention icon: still caches an SVG icon', async function () {
        const bytes = h.unsafeSvg();
        const externalRequest = () => ({
            buffer: async () => bytes,
            headers: { 'content-type': 'image/svg+xml' },
        });
        externalRequest.head = sinon.stub().resolves({});

        const service = new OEmbedService({
            config,
            externalRequest,
            imageStore: adapterManager.getAdapter('storage:images'),
        });

        const bookmark = await service.buildBookmarkData(
            'https://publisher.example/page',
            { title: 'A page', icon: 'https://publisher.example/icon.svg' },
            'mention',
        );

        const stored = h.storedIn(path.join(tmp, 'content'), 'images');
        assert.equal(stored.length, 1, 'the SVG icon was dropped');
        assert.ok(stored[0].endsWith('.svg'), 'the SVG icon was not cached as an SVG');
        assert.ok(fs.readFileSync(stored[0], 'utf8').includes('<svg'), 'the SVG icon was not stored');
        assert.equal(bookmark.metadata.icon.startsWith('/content/images/icon/'), true);
    });

    it('mention icon: keeps the bookmark when the icon cannot be fetched', async function () {
        const externalRequest = () => {
            throw new Error('unreachable');
        };
        externalRequest.head = sinon.stub().resolves({});

        const service = new OEmbedService({
            config,
            externalRequest,
            imageStore: adapterManager.getAdapter('storage:images'),
        });

        const bookmark = await service.buildBookmarkData(
            'https://publisher.example/page',
            { title: 'A page', icon: 'https://publisher.example/icon.png' },
            'mention',
        );

        assert.equal(bookmark.metadata.icon, 'https://publisher.example/icon.png');
        assert.deepEqual(h.storedIn(path.join(tmp, 'content'), 'images'), []);
    });
});
