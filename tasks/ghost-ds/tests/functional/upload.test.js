// Direct image uploads keep accepting real images, and SVG uploads are still
// stored sanitized.
const assert = require('node:assert/strict');
const { describe, it, beforeEach, afterEach } = require('node:test');
const fs = require('node:fs');
const express = require('express');
const request = require('supertest');

const h = require('../helpers');
const upload = require('../../../core/server/web/api/middleware/upload');

describe('image uploads', () => {
    const app = express();
    app.post(
        '/images/upload',
        upload.single('file'),
        upload.validation({ type: 'images' }),
        (req, res) => {
            res.status(201).json({ content: fs.readFileSync(req.file.path, 'utf8') });
        },
    );
    app.use((err, req, res, next) => {
        res.status(err.statusCode || 500).json({ refused: true });
    });

    for (const [fixture, filename, contentType] of [
        ['ghosticon.jpg', 'photo.jpg', 'image/jpeg'],
        ['ghost-logo.png', 'logo.png', 'image/png'],
        ['loadingcat.gif', 'anim.gif', 'image/gif'],
        ['ghosticon.webp', 'pic.webp', 'image/webp'],
    ]) {
        it(`upload: accepts a real ${filename}`, async function () {
            const response = await request(app)
                .post('/images/upload')
                .attach('file', h.fixture(fixture), { filename, contentType });

            assert.equal(response.status, 201);
        });
    }

    it('upload: accepts a real SVG and stores it sanitized', async function () {
        const response = await request(app)
            .post('/images/upload')
            .attach('file', h.unsafeSvg(), {
                filename: 'logo.svg',
                contentType: 'image/svg+xml',
            });

        assert.equal(response.status, 201);
        assert.ok(response.body.content.includes('<svg'), 'the SVG was dropped');
        assert.equal(response.body.content.includes('<script'), false, 'the SVG was not sanitized');
    });
});
