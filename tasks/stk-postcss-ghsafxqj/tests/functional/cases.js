'use strict';

/*
 * Functional cases: legitimate previous-map use and the coupled values next to the hidden ones.
 * Every expectation below is what the pinned library already produces today; these must keep
 * working whatever the fix does. Expected values are literals written here; nothing is computed
 * with the product.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { pathToFileURL } = require('url');

const MARK = {
  inside: 'POSTCSS_TASK_FUNC_INSIDE_1d7a',
  nested: 'POSTCSS_TASK_FUNC_NESTED_3c9b',
  string: 'POSTCSS_TASK_FUNC_STRING_5e2f',
  trusted: 'POSTCSS_TASK_FUNC_TRUSTED_8a4c',
  inline: 'POSTCSS_TASK_FUNC_INLINE_6b0d',
  origin: 'POSTCSS_TASK_FUNC_ORIGIN_2f8e'
};

function mapWith(sources, content) {
  return JSON.stringify({
    version: 3,
    sources,
    names: [],
    mappings: 'AAAA',
    sourcesContent: [content]
  });
}

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'postcss-func-'));
  const inside = path.join(root, 'inside');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(inside);
  fs.mkdirSync(outside);
  fs.mkdirSync(path.join(inside, 'maps'));
  return { root, inside, outside };
}

function cleanup(root) {
  try {
    fs.rmSync(root, { force: true, recursive: true });
  } catch (_) {
    /* best effort */
  }
}

function mapJson(result) {
  if (!result.map) return '';
  try {
    return JSON.stringify(result.map.toJSON());
  } catch (_) {
    return String(result.map);
  }
}

function functionalCase(id, name, run) {
  return { classname: 'functional/' + id, name: `${id}: ${name}`, run };
}

module.exports = function (postcss) {
  const cases = [];

  // A previous map named by a real annotation, next to the stylesheet, still loads and is applied.
  cases.push(functionalCase('F-inside-annotation', 'an in-folder previous map is applied', () => {
    const f = fixture();
    try {
      fs.writeFileSync(path.join(f.inside, 'prev.map'), mapWith(['orig.scss'], MARK.inside));
      const result = postcss([() => {}]).process(
        'a{color:red}\n/*# sourceMappingURL=prev.map */',
        { from: path.join(f.inside, 'in.css'), map: { inline: false } }
      );
      if (!mapJson(result).includes(MARK.inside)) {
        throw new Error('the in-folder previous map was not applied');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // A previous map in a sub-folder of the stylesheet's folder still loads.
  cases.push(functionalCase('F-nested-annotation', 'a previous map in a sub-folder is applied', () => {
    const f = fixture();
    try {
      fs.writeFileSync(path.join(f.inside, 'maps', 'nested.map'), mapWith(['n.scss'], MARK.nested));
      const result = postcss([() => {}]).process(
        'a{color:red}\n/*# sourceMappingURL=maps/nested.map */',
        { from: path.join(f.inside, 'in.css'), map: { inline: false } }
      );
      if (!mapJson(result).includes(MARK.nested)) {
        throw new Error('the sub-folder previous map was not applied');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // A previous map supplied by the caller as text still applies.
  cases.push(functionalCase('F-prev-string', 'a caller-supplied map text still applies', () => {
    const f = fixture();
    try {
      const result = postcss([() => {}]).process('a{color:red}', {
        from: path.join(f.inside, 'in.css'),
        map: { inline: false, prev: mapWith(['p.scss'], MARK.string) }
      });
      if (!mapJson(result).includes(MARK.string)) {
        throw new Error('the caller-supplied map text was not applied');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // A previous map loaded by a caller-supplied loader still applies, wherever it points.
  cases.push(functionalCase('F-prev-function', 'a caller-supplied map loader still applies', () => {
    const f = fixture();
    try {
      const elsewhere = path.join(f.outside, 'trusted.dat');
      fs.writeFileSync(elsewhere, mapWith(['t.scss'], MARK.trusted));
      const result = postcss([() => {}]).process('a{color:red}', {
        from: path.join(f.inside, 'in.css'),
        map: { inline: false, prev: () => elsewhere }
      });
      if (!mapJson(result).includes(MARK.trusted)) {
        throw new Error('the caller-supplied map loader was not applied');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // An inline data map still applies when the stylesheet has no file.
  cases.push(functionalCase('F-inline-map', 'an inline data map still applies without a file', () => {
    const encoded = Buffer.from(mapWith(['i.scss'], MARK.inline)).toString('base64');
    const result = postcss([() => {}]).process(
      `a{color:red}\n/*# sourceMappingURL=data:application/json;base64,${encoded} */`,
      { map: { inline: false } }
    );
    if (!mapJson(result).includes(MARK.inline)) {
      throw new Error('the inline data map was not applied');
    }
  }));

  // A caller who asks to keep the input annotation still gets it.
  cases.push(functionalCase('F-keep-annotation', 'the input annotation is kept when asked', () => {
    const f = fixture();
    try {
      const result = postcss([() => {}]).process(
        'a{color:red}\n/*# sourceMappingURL=input.map */',
        { from: path.join(f.inside, 'in.css'), map: { annotation: false, inline: false } }
      );
      if (!result.css.includes('/*# sourceMappingURL=input.map */')) {
        throw new Error('the caller-requested input annotation was dropped');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // Ordinary CSS content that happens to contain the annotation text is emitted unchanged.
  cases.push(functionalCase('F-string-content', 'ordinary CSS content is emitted unchanged', () => {
    const f = fixture();
    try {
      const css =
        'a{content:"/*# sourceMappingURL=keep.me */"}\n/*#region fold */\nb{color:blue}';
      const result = postcss([() => {}]).process(css, { from: path.join(f.inside, 'in.css') });
      if (!result.css.includes('/*# sourceMappingURL=keep.me */')) {
        throw new Error('string content that only resembles an annotation was rewritten');
      }
      if (!result.css.includes('/*#region fold */')) {
        throw new Error('an ordinary comment was dropped');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // Asking for a map still produces the library's own annotation.
  cases.push(functionalCase('F-generated-annotation', 'asking for a map still emits its annotation', () => {
    const f = fixture();
    try {
      const result = postcss([() => {}]).process('a{color:red}', {
        from: path.join(f.inside, 'in.css'),
        map: true
      });
      if (!/sourceMappingURL=data:application\/json/.test(result.css)) {
        throw new Error('the generated map annotation is missing');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // A caller-supplied loader that cannot produce a map still raises the documented error.
  cases.push(functionalCase('F-prev-error', 'an unusable caller-supplied map still raises', () => {
    const f = fixture();
    try {
      let raised = null;
      try {
        postcss([() => {}]).process('a{}', {
          from: path.join(f.inside, 'in.css'),
          map: { prev: () => path.join(f.inside, 'nope.map') }
        }).css;
      } catch (e) {
        raised = e;
      }
      if (!raised || !/Unable to load previous source map/.test(String(raised.message || raised))) {
        throw new Error('an unusable caller-supplied map did not raise the documented error');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // Map sources legitimately point outside the stylesheet's folder and are reported as such.
  cases.push(functionalCase('F-origin-sources', 'map sources outside the folder are resolved', () => {
    const f = fixture();
    try {
      fs.writeFileSync(
        path.join(f.inside, 'maps', 'outside.map'),
        mapWith(['../../outside/x.scss'], MARK.origin)
      );
      const root = postcss.parse(
        'a{color:red}\n/*# sourceMappingURL=maps/outside.map */',
        { from: path.join(f.inside, 'in.css') }
      );
      const origin = root.source.input.origin(1, 1);
      const expected = path.join(f.outside, 'x.scss');
      if (origin.file !== expected) {
        throw new Error(`origin.file is ${JSON.stringify(origin.file)}, expected ${JSON.stringify(expected)}`);
      }
      if (origin.url !== pathToFileURL(expected).href) {
        throw new Error(`origin.url is ${JSON.stringify(origin.url)}, expected ${JSON.stringify(pathToFileURL(expected).href)}`);
      }
      if (origin.source !== MARK.origin) {
        throw new Error('the map source content was not carried through');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  // The no-plugin path already removed an input annotation; that behaviour stays.
  cases.push(functionalCase('F-no-plugin-annotation', 'the no-plugin path still drops the input annotation', () => {
    const f = fixture();
    try {
      const result = postcss([]).process(
        'a{color:red}\n/*# sourceMappingURL=missing.map */',
        { from: path.join(f.inside, 'in.css') }
      );
      if (/sourceMappingURL/.test(result.css)) {
        throw new Error('the input annotation survived the no-plugin path');
      }
      if (!result.css.includes('color:red')) {
        throw new Error('the declaration was dropped');
      }
    } finally {
      cleanup(f.root);
    }
  }));

  return cases;
};
