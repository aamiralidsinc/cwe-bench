'use strict';

/*
 * Control security cases: the advisory's own route only. An annotation supplied with untrusted
 * CSS must not make the processor read a file outside the stylesheet's folder. Expected values are
 * literal markers written here; nothing is computed with the product.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const MARK = 'POSTCSS_CONTROL_SECRET_5c3a';

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
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'postcss-control-'));
  const inside = path.join(root, 'inside');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(inside);
  fs.mkdirSync(outside);
  fs.mkdirSync(path.join(outside, 'deep'));
  fs.mkdirSync(path.join(inside, 'deep'));
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

function caseFor(postcss, id, setup) {
  return {
    classname: 'security/' + id,
    name: `${id}: untrusted annotation does not read ${MARK}`,
    run() {
      const f = fixture();
      try {
        const spec = setup(f);
        let result;
        try {
          result = postcss([() => {}]).process(spec.css, spec.options);
        } catch (e) {
          const message = String((e && (e.message || e)) || '');
          if (message.includes(MARK)) {
            throw new Error('the refused operation still exposed the protected file contents');
          }
          return;
        }
        if (outputText(result).includes(MARK)) {
          throw new Error('the processor read a file the untrusted annotation selected');
        }
      } finally {
        cleanup(f.root);
      }
    }
  };
}

module.exports = function (postcss) {
  const cases = [];

  cases.push(caseFor(postcss, 'T1-absolute-no-file', f => {
    const secret = path.join(f.outside, 'secret.map');
    fs.writeFileSync(secret, mapWith(MARK));
    return {
      css: `a{color:red}\n/*# sourceMappingURL=${secret} */`,
      options: { map: { inline: false } }
    };
  }));

  cases.push(caseFor(postcss, 'T1-absolute-deep', f => {
    const secret = path.join(f.outside, 'deep', 'secret.map');
    fs.writeFileSync(secret, mapWith(MARK));
    return {
      css: `a{color:red}\n/*# sourceMappingURL=${secret} */`,
      options: { map: { inline: false } }
    };
  }));

  cases.push(caseFor(postcss, 'T1-traversal-with-file', f => {
    fs.writeFileSync(path.join(f.outside, 'secret.map'), mapWith(MARK));
    return {
      css: 'a{color:red}\n/*# sourceMappingURL=../outside/secret.map */',
      options: { from: path.join(f.inside, 'in.css'), map: { inline: false } }
    };
  }));

  cases.push(caseFor(postcss, 'T1-traversal-subdir', f => {
    fs.writeFileSync(path.join(f.outside, 'secret.map'), mapWith(MARK));
    return {
      css: 'a{color:red}\n/*# sourceMappingURL=../../outside/secret.map */',
      options: { from: path.join(f.inside, 'deep', 'in.css'), map: { inline: false } }
    };
  }));

  return cases;
};
