'use strict';

/*
 * Control security cases: only the advisory's own route, a source object that owns a __proto__ key
 * merged recursively into a destination. A refusal (a thrown error) counts as blocked; what matters
 * is that nothing outside the destination changed. Every marker is removed in a finally block.
 */

function assertNoMarker(marker, how) {
  if (marker in {}) {
    throw new Error(`${how} left ${marker} reachable from every object`);
  }
  if (Object.prototype[marker] !== undefined) {
    throw new Error(`${how} wrote ${marker} onto Object.prototype`);
  }
}

function attempt(fn) {
  try {
    fn();
  } catch (e) {
    // a refusal with an error is acceptable; the side-effect assertion decides
  }
}

module.exports = function (product) {
  const { deepMixIn } = product;
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: 'security/' + id, name, run });

  add('mix-own-proto', 'a source owning a __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutCtlMixTop';
    try {
      const source = JSON.parse('{"__proto__":{"' + marker + '":"x"}}');
      attempt(() => deepMixIn({}, source));
      assertNoMarker(marker, 'deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('mix-nested-proto', 'a nested __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutCtlMixNested';
    try {
      const target = { group: {} };
      const source = JSON.parse('{"group":{"__proto__":{"' + marker + '":"x"}}}');
      attempt(() => deepMixIn(target, source));
      assertNoMarker(marker, 'nested deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('mix-later-source', 'a later source argument is guarded like the first', function () {
    const marker = 'moutCtlMixSecond';
    try {
      const source = JSON.parse('{"__proto__":{"' + marker + '":"x"}}');
      attempt(() => deepMixIn({ first: 1 }, { second: 2 }, source));
      assertNoMarker(marker, 'multi-source deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('mix-defined-proto', 'an own __proto__ key defined explicitly is guarded too', function () {
    const marker = 'moutCtlMixDefined';
    try {
      const source = {};
      Object.defineProperty(source, '__proto__', {
        value: JSON.parse('{"' + marker + '":"x"}'), enumerable: true, configurable: true, writable: true,
      });
      attempt(() => deepMixIn({}, source));
      assertNoMarker(marker, 'deep merge of a defined __proto__ key');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('mix-deep-proto', 'a deeply nested __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutCtlMixDeep';
    try {
      const target = { a: { b: {} } };
      const source = JSON.parse('{"a":{"b":{"__proto__":{"' + marker + '":"x"}}}}');
      attempt(() => deepMixIn(target, source));
      assertNoMarker(marker, 'deeply nested deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  return cases;
};
