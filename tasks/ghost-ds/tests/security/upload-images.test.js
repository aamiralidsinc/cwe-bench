// Image uploads are chosen by the client's file name and media type. The
// bytes themselves must also be an allowed image.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const express = require('express');
const request = require('supertest');

const h = require('../helpers');
const upload = require('../../../core/server/web/api/middleware/upload');

describe('image upload contents', () => {
    let stored;

    const app = express();
    app.post(
        '/images/upload',
        upload.single('file'),
        upload.validation({ type: 'images' }),
        (req, res) => {
            stored = true;
            res.status(201).json({ accepted: true });
        },
    );
    app.use((err, req, res, next) => {
        res.status(err.statusCode || 500).json({ refused: true });
    });

    beforeEach(function () {
        stored = false;
    });

    it('upload: refuses SVG bytes named as a raster image', async function () {
        const response = await request(app)
            .post('/images/upload')
            .attach('file', h.unsafeSvg(), { filename: 'attack.png', contentType: 'image/png' });

        assert.ok(response.status >= 400 && response.status < 500, `got ${response.status}`);
        assert.equal(stored, false, 'the upload reached image storage');
    });

    it('upload: refuses non-image bytes named as a raster image', async function () {
        const response = await request(app)
            .post('/images/upload')
            .attach('file', h.textPayload(), { filename: 'attack.jpg', contentType: 'image/jpeg' });

        assert.ok(response.status >= 400 && response.status < 500, `got ${response.status}`);
        assert.equal(stored, false, 'the upload reached image storage');
    });

    it('upload: refuses an unaccepted image format', async function () {
        const sharp = require('sharp');
        const avif = await sharp({
            create: { width: 8, height: 8, channels: 3, background: 'red' },
        })
            .avif()
            .toBuffer();

        const response = await request(app)
            .post('/images/upload')
            .attach('file', avif, { filename: 'attack.jpg', contentType: 'image/jpeg' });

        assert.ok(response.status >= 400 && response.status < 500, `got ${response.status}`);
        assert.equal(stored, false, 'the upload reached image storage');
    });
});
