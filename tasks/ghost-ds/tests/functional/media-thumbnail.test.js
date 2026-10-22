// Real media uploads keep their video and their thumbnail, and a vector
// thumbnail is still accepted after its active content is removed.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const express = require('express');
const request = require('supertest');

const h = require('../helpers');
const upload = require('../../../core/server/web/api/middleware/upload');
const mediaApi = require('../../../core/server/api/endpoints/media');

describe('media thumbnails', () => {
    let tmp;
    let app;
    const video = Buffer.from('CWE_GHOST_DS_VIDEO');

    beforeEach(function () {
        tmp = h.tempDir();
        h.useTempContentPath(tmp);
        app = express();
        app.post(
            '/media/upload',
            upload.media('file', 'thumbnail'),
            upload.mediaValidation({ type: 'media' }),
            async (req, res, next) => {
                try {
                    const result = await mediaApi.upload.query({ files: req.files });
                    res.status(201).json(result);
                } catch (err) {
                    next(err);
                }
            },
        );
        app.use((err, req, res, next) => {
            res.status(err.statusCode || 500).json({ refused: true });
        });
    });

    afterEach(async function () {
        await h.restoreConfig();
        fs.rmSync(tmp, { recursive: true, force: true });
    });

    const send = (bytes, filename, contentType) =>
        request(app)
            .post('/media/upload')
            .attach('file', video, { filename: 'movie.mp4', contentType: 'video/mp4' })
            .attach('thumbnail', bytes, { filename, contentType });

    it('media upload: stores a real video and its image thumbnail', async function () {
        const thumb = h.fixture('ghost-logo.png');
        const response = await send(thumb, 'thumb.png', 'image/png');

        assert.equal(response.status, 201);

        const stored = h.storedIn(path.join(tmp, 'content'), 'media');
        const thumbnail = stored.find((file) => path.basename(file).endsWith('_thumb.png'));
        assert.ok(thumbnail, 'the thumbnail was not stored');
        assert.deepEqual(fs.readFileSync(thumbnail), thumb);
        assert.ok(
            stored.some((file) => path.basename(file) === 'movie.mp4'),
            'the media file was not stored',
        );
    });

    it('media upload: still stores a vector thumbnail after sanitizing it', async function () {
        const response = await send(h.unsafeSvg(), 'thumb.svg', 'image/svg+xml');

        assert.equal(response.status, 201);

        const thumbnail = h
            .storedIn(path.join(tmp, 'content'), 'media')
            .find((file) => path.basename(file).endsWith('_thumb.svg'));
        assert.ok(thumbnail, 'the vector thumbnail was dropped');
        const body = fs.readFileSync(thumbnail, 'utf8');
        assert.ok(body.includes('<svg'), 'the vector thumbnail was not stored as an image');
        assert.equal(body.includes('<script'), false, 'the vector thumbnail was not sanitized');
    });
});
