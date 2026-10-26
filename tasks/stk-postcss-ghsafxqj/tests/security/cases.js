'use strict';

/*
 * Security cases. Each case drives the library's public entry point on untrusted CSS and then
 * checks the protected outcome: a local file outside the stylesheet's folder must not be read, a
 * map file must only be selected by a genuine annotation comment, and an annotation supplied with
 * the input must not be carried into the emitted CSS. Expected values are literal markers written
 * here; nothing is computed with the product.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const MARK = {
  outside: 'POSTCSS_TASK_SECRET_OUTSIDE_7c1f',
  inside: 'POSTCSS_TASK_SECRET_INSIDE_4b8e',
  outsideDir: 'POSTCSS_TASK_SECRET_DIRLINK_9a2d'
};

function mapWith(marker) {
  return JSON.stringify({
    version: 3,
    sources: ['s.scss'],
    names: [],
    mappings: 'AAAA',
    sourcesContent: [marker]
  });
}

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'postcss-case-'));
  const inside = path.join(root, 'inside');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(inside);
  fs.mkdirSync(outside);
  return { root, inside, outside };
}

function cleanup(root) {
  try {
    fs.rmSync(root, { force: true, recursive: true });
  } catch (_) {
    /* best effort */
  }
}

function outputText(result) {
  let text = String(result.css || '');
  if (result.map) {
    try {
      text += '\n' + JSON.stringify(result.map.toJSON());
    } catch (_) {
      text += '\n' + String(result.map);
    }
  }
  return text;
}

/* Process CSS and fail when the protected marker reaches the output or an error. A thrown error
 * is accepted as a refusal only when it does not carry the protected contents. */
function assertNotDisclosed(postcss, id, css, opts, marker) {
  return {
    classname: 'security/' + id,
    name: `${id}: untrusted annotation does not disclose ${marker}`,
    run() {
      const f = fixture();
      try {
        const setup = opts(f);
        let result;
        try {
          result = postcss([() => {}]).process(setup.css, setup.options);
        } catch (e) {
          const message = String((e && (e.message || e)) || '');
          if (message.includes(marker)) {
            throw new Error('the refused operation still exposed the protected file contents');
          }
          return;
        }
        const text = outputText(result);
        if (text.includes(marker)) {
          throw new Error('the processor read a file the untrusted annotation selected');
        }
      } finally {
        cleanup(f.root);
      }
    }
  };
}

function emittedAnnotationCase(postcss, id, css) {
  return {
    classname: 'security/' + id,
    name: `${id}: the input annotation is not carried into the emitted CSS`,
    run() {
      let result;
      try {
        result = postcss([() => {}]).process(css, {
          from: path.join(os.tmpdir(), 'postcss-case-emit', 'in.css')
        });
      } catch (e) {
        return; // a clean refusal emits nothing
      }
      const text = String(result.css || '');
      if (/sourceMappingURL/i.test(text)) {
        throw new Error('the untrusted source-map annotation survived into the emitted CSS');
      }
      if (!text.includes('color:red')) {
        throw new Error('the legitimate declaration was dropped from the emitted CSS');
      }
    }
  };
}

module.exports = function (postcss) {
  const cases = [];

  // The reported route: an annotation selects a file outside the stylesheet's folder.
  cases.push(assertNotDisclosed(postcss, 'T1-absolute-no-file', null, f => {
    const secret = path.join(f.outside, 'secret.map');
    fs.writeFileSync(secret, mapWith(MARK.outside));
    return {
      css: `a{color:red}\n/*# sourceMappingURL=${secret} */`,
      options: { map: { inline: false } }
    };
  }, MARK.outside));

  cases.push(assertNotDisclosed(postcss, 'T1-traversal-with-file', null, f => {
    fs.writeFileSync(path.join(f.outside, 'secret.map'), mapWith(MARK.outside));
    return {
      css: 'a{color:red}\n/*# sourceMappingURL=../outside/secret.map */',
      options: { from: path.join(f.inside, 'in.css'), map: { inline: false } }
    };
  }, MARK.outside));

  // A path that looks contained but resolves outside through a symbolic link.
  cases.push(assertNotDisclosed(postcss, 'T10-symlink-file', null, f => {
    const secret = path.join(f.outside, 'secret.map');
    fs.writeFileSync(secret, mapWith(MARK.outside));
    fs.symlinkSync(secret, path.join(f.inside, 'link.map'));
    return {
      css: 'a{color:red}\n/*# sourceMappingURL=link.map */',
      options: { from: path.join(f.inside, 'in.css'), map: { inline: false } }
    };
  }, MARK.outside));

  cases.push(assertNotDisclosed(postcss, 'T10-symlink-directory', null, f => {
    fs.writeFileSync(path.join(f.outside, 'secret.map'), mapWith(MARK.outsideDir));
    fs.symlinkSync(f.outside, path.join(f.inside, 'maps'));
    return {
      css: 'a{color:red}\n/*# sourceMappingURL=maps/secret.map */',
      options: { from: path.join(f.inside, 'in.css'), map: { inline: false } }
    };
  }, MARK.outsideDir));

  // Marker text that is ordinary CSS content, not an annotation comment, must not select a map.
  cases.push(assertNotDisclosed(postcss, 'T2-marker-in-string', null, f => {
    fs.writeFileSync(path.join(f.inside, 'prev.map'), mapWith(MARK.inside));
    return {
      css: 'a{content:"/*# sourceMappingURL=prev.map */"}',
      options: { from: path.join(f.inside, 'in.css'), map: { inline: false } }
    };
  }, MARK.inside));

  cases.push(assertNotDisclosed(postcss, 'T2-marker-in-selector', null, f => {
    fs.writeFileSync(path.join(f.inside, 'prev.map'), mapWith(MARK.inside));
    return {
      css: 'a[data-x="/*# sourceMappingURL=prev.map */"]{color:red}',
      options: { from: path.join(f.inside, 'in.css'), map: { inline: false } }
    };
  }, MARK.inside));

  // An annotation supplied with the input must not be passed on in the emitted CSS.
  cases.push(emittedAnnotationCase(postcss, 'T3-emitted-annotation', (
    'a{color:red}\n/*# sourceMappingURL=../postcss-missing-dir-7c1f/missing.map */'
  )));
  cases.push(emittedAnnotationCase(postcss, 'T3-emitted-annotation-top', (
    '/*# sourceMappingURL=/nonexistent-postcss-task/missing.map */a{color:red}'
  )));

  return cases;
};
