'use strict';

// Bookkeeping for documents that carry a marker. A value that reaches generated
// code would run the marker; the tests only check whether it ran.

const PROBE = '__document_probe_value__';

function resetProbe() {
  delete globalThis[PROBE];
}

function probeRan() {
  return Object.prototype.hasOwnProperty.call(globalThis, PROBE);
}

function location() {
  return {
    source: null,
    start: { line: 1, column: 0 },
    end: { line: 1, column: 8 }
  };
}

function pathNode(parts, extra) {
  const node = {
    type: 'PathExpression',
    data: false,
    depth: 0,
    parts: parts,
    original: parts.length ? parts.join('.') : '',
    loc: location()
  };
  return Object.assign(node, extra || {});
}

function program(body, extra) {
  return Object.assign(
    { type: 'Program', body: body, loc: location() },
    extra || {}
  );
}

function mustache(path, params, extra) {
  return Object.assign(
    {
      type: 'MustacheStatement',
      escaped: true,
      strip: { open: false, close: false },
      path: path,
      params: params || [],
      loc: location()
    },
    extra || {}
  );
}

// Run something that may legitimately be refused; a refusal is an acceptable
// outcome, the marker check is what decides the test.
function attempt(fn) {
  try {
    fn();
  } catch (err) {
    return err;
  }
  return null;
}

module.exports = {
  resetProbe,
  probeRan,
  location,
  pathNode,
  program,
  mustache,
  attempt
};
