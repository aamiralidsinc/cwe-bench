// Shared helpers for the hidden tests. Everything here is test-side: fixture
// bytes, temp directories, and storage inspection. No product code is used to
// compute an expected value.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');

const FIXTURES = path.join(__dirname, 'fixtures');
const IMAGES = path.join(FIXTURES, 'images');

// A harmless marker placed in attack payloads. A correct fix must keep it out
// of image storage.
const MARKER = 'CWE_GHOST_DS_MARKER_92f4';

function tempDir(prefix = 'ghost-ds-') {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function unsafeSvg(marker = MARKER) {
    // The marker appears in a script, in an event-handler attribute and in an
    // embedded document, so a sanitizer that only strips one shape leaves it
    // behind.
    return Buffer.from(
        `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" onload="window.${marker} = 1">` +
            `<rect width="20" height="20" fill="blue"/>` +
            `<script type="text/javascript">window.${marker} = 1;</script>` +
            `<foreignObject width="20" height="20">` +
            `<iframe xmlns="http://www.w3.org/1999/xhtml" src="javascript:window.${marker} = 1"></iframe>` +
            `</foreignObject>` +
            `</svg>`,
        'utf8',
    );
}

function unsafeSvgz() {
    return zlib.gzipSync(unsafeSvg());
}

function textPayload() {
    return Buffer.from(`This is not an image. ${MARKER}`, 'utf8');
}

function fixture(name) {
    return fs.readFileSync(path.join(IMAGES, name));
}

function fixturePath(name) {
    return path.join(IMAGES, name);
}

function walk(dir) {
    if (!fs.existsSync(dir)) {
        return [];
    }

    const out = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            out.push(...walk(full));
        } else {
            out.push(full);
        }
    }
    return out;
}

function readMaybeZipped(file) {
    const bytes = fs.readFileSync(file);
    if (file.endsWith('.svgz')) {
        try {
            return zlib.gunzipSync(bytes);
        } catch {
            return bytes;
        }
    }
    return bytes;
}

/** Files under the image store whose (decompressed) content contains marker. */
function storageLeaks(tmp, marker = MARKER) {
    const contentPath = path.join(tmp, 'content');
    const root = path.join(contentPath, 'images');
    return walk(root)
        .filter((file) => readMaybeZipped(file).includes(marker))
        .map((file) => path.relative(contentPath, file));
}

/**
 * Files anywhere under the content directory (image, media and file storage)
 * whose (decompressed) content contains marker. A rejected file that is moved
 * to another storage instead of being refused still shows up here.
 */
function contentLeaks(tmp, marker = MARKER) {
    const contentPath = path.join(tmp, 'content');
    return walk(contentPath)
        .filter((file) => readMaybeZipped(file).includes(marker))
        .map((file) => path.relative(contentPath, file));
}

/** Stored image file names (relative to the image store). */
function storedImageNames(tmp) {
    const contentPath = path.join(tmp, 'content');
    const root = path.join(contentPath, 'images');
    return walk(root).map((file) => path.relative(contentPath, file));
}

function storedIn(contentPath, collection) {
    return walk(path.join(contentPath, collection));
}

/**
 * Point the local storage adapters at a temp content directory. Call before
 * the first storage adapter use in a test.
 */
function useTempContentPath(tmp) {
    const configUtils = require('../utils/config-utils');
    const adapterManager = require('../../core/server/services/adapter-manager').default;
    configUtils.set('paths:contentPath', path.join(tmp, 'content'));
    adapterManager.clearCache();
    return path.join(tmp, 'content');
}

async function restoreConfig() {
    const configUtils = require('../utils/config-utils');
    await configUtils.restore();
}

let zipCounter = 0;

/**
 * Write files into a directory and compress it into an import zip.
 *
 * @param {string} tmp
 * @param {Record<string, Buffer|string>} files - archive-relative paths
 * @param {string} [dataFile] - name of a JSON data file to add (a minimal export)
 * @returns {Promise<{zipPath: string, sourceDir: string}>}
 */
async function buildZip(tmp, files, dataFile = 'posts.json') {
    const { compress } = require('@tryghost/zip');
    zipCounter += 1;
    const sourceDir = path.join(tmp, `zip-src-${zipCounter}`);
    const zipPath = path.join(tmp, `import-${zipCounter}.zip`);

    for (const [name, bytes] of Object.entries(files)) {
        const target = path.join(sourceDir, name);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.writeFileSync(target, bytes);
    }

    if (dataFile) {
        const target = path.join(sourceDir, dataFile);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        const body = dataFile.endsWith('.csv')
            ? 'title,slug,published\nA post,a-post,true\n'
            : JSON.stringify({ db: [{ data: {} }] });
        fs.writeFileSync(target, body);
    }

    await compress(sourceDir, zipPath);
    return { zipPath, sourceDir };
}

module.exports = {
    FIXTURES,
    IMAGES,
    MARKER,
    buildZip,
    contentLeaks,
    fixture,
    fixturePath,
    readMaybeZipped,
    restoreConfig,
    storageLeaks,
    storedImageNames,
    storedIn,
    tempDir,
    textPayload,
    unsafeSvg,
    unsafeSvgz,
    useTempContentPath,
    walk,
};
