// A media upload carries a thumbnail, and that thumbnail is stored and served
// as an image. Its bytes must be an allowed image even though the upload is
// nominally about a video.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const express = require('express');
const request = require('supertest');

const h = require('../helpers');
const upload = require('../../../core/server/web/api/middleware/upload');
const mediaApi = require('../../../core/server/api/endpoints/media');

describe('media thumbnail contents', () => {
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

    it('media upload: does not store SVG bytes as a thumbnail', async function () {
        await send(h.unsafeSvg(), 'thumb.png', 'image/png');

        assert.deepEqual(h.contentLeaks(tmp), []);
    });

    it('media upload: does not store non-image bytes as a thumbnail', async function () {
        await send(h.textPayload(), 'thumb.jpg', 'image/jpeg');

        assert.deepEqual(h.contentLeaks(tmp), []);
    });

    it('media upload: does not store an unaccepted image format as a thumbnail', async function () {
        const sharp = require('sharp');
        const avif = await sharp({
            create: { width: 8, height: 8, channels: 3, background: 'red' },
        })
            .avif()
            .toBuffer();

        await send(avif, 'thumb.jpg', 'image/jpeg');

        const stored = h
            .walk(path.join(tmp, 'content'))
            .filter((file) => fs.readFileSync(file).equals(avif))
            .map((file) => path.relative(path.join(tmp, 'content'), file));
        assert.deepEqual(stored, [], 'an image format the site does not accept was stored');
    });
});
