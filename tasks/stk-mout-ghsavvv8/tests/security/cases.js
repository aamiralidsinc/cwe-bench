'use strict';

/*
 * Security cases: caller-supplied input must not reach a shared prototype object, whichever public
 * helper carries it. Each case creates at most one marker on Object.prototype only when the helper
 * needs an existing shared property to act on, and removes it again in a finally block. A refusal
 * (a thrown error) counts as blocked; what matters is that nothing outside the destination changed.
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
    // A refusal with an error is acceptable; the side-effect assertion below decides.
  }
}

module.exports = function (product) {
  const { deepMixIn, deepFillIn, set, namespace, unset } = product;
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: 'security/' + id, name, run });

  // --- own-key copy into an existing destination -------------------------------------
  add('deep-mix-in-own-proto', 'deep copy of a source owning a __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutSecMixTop';
    try {
      const source = JSON.parse('{"__proto__":{"' + marker + '":"x"}}');
      attempt(() => deepMixIn({}, source));
      assertNoMarker(marker, 'deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('deep-mix-in-nested-proto', 'deep copy of a nested __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutSecMixNested';
    try {
      const target = { group: {} };
      const source = JSON.parse('{"group":{"__proto__":{"' + marker + '":"x"}}}');
      attempt(() => deepMixIn(target, source));
      assertNoMarker(marker, 'nested deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('deep-mix-in-later-source', 'a later source argument is guarded like the first', function () {
    const marker = 'moutSecMixSecond';
    try {
      const source = JSON.parse('{"__proto__":{"' + marker + '":"x"}}');
      attempt(() => deepMixIn({ first: 1 }, { second: 2 }, source));
      assertNoMarker(marker, 'multi-source deep merge');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('deep-fill-in-own-proto', 'deep fill of defaults owning a __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutSecFillTop';
    try {
      const defaults = JSON.parse('{"__proto__":{"' + marker + '":"x"}}');
      attempt(() => deepFillIn({}, defaults));
      assertNoMarker(marker, 'deep fill');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('deep-fill-in-nested-proto', 'deep fill of a nested __proto__ key does not reach Object.prototype', function () {
    const marker = 'moutSecFillNested';
    try {
      const target = { group: { keep: 1 } };
      const defaults = JSON.parse('{"group":{"__proto__":{"' + marker + '":"x"}}}');
      attempt(() => deepFillIn(target, defaults));
      assertNoMarker(marker, 'nested deep fill');
    } finally {
      delete Object.prototype[marker];
    }
  });

  // --- dotted-path writers -----------------------------------------------------------
  add('set-constructor-prototype', 'a dotted path through the inherited constructor does not write a shared prototype', function () {
    const marker = 'moutSecSetCtor';
    try {
      attempt(() => set({}, 'constructor.prototype.' + marker, 'x'));
      assertNoMarker(marker, 'dotted set');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('set-proto-segment', 'a path whose first segment is __proto__ does not write a shared prototype', function () {
    const marker = 'moutSecSetProto';
    try {
      attempt(() => set({}, '__proto__.' + marker, 'x'));
      assertNoMarker(marker, 'dotted set through __proto__');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('set-non-string-path', 'a dotted path supplied in a non-string form does not write a shared prototype', function () {
    const marker = 'moutSecSetArray';
    try {
      attempt(() => set({}, ['constructor.prototype.' + marker], 'x'));
      assertNoMarker(marker, 'dotted set with a non-string path');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('namespace-constructor-prototype', 'creating a namespace cannot follow an inherited constructor', function () {
    const marker = 'moutSecNsCtor';
    try {
      attempt(() => namespace({}, 'plain.constructor.prototype.' + marker));
      assertNoMarker(marker, 'namespace through constructor');
    } finally {
      delete Object.prototype[marker];
    }
  });

  add('namespace-proto-segment', 'creating a namespace cannot follow an inherited __proto__ segment', function () {
    const marker = 'moutSecNsProto';
    try {
      attempt(() => namespace({}, 'plain.__proto__.' + marker));
      assertNoMarker(marker, 'namespace through __proto__');
    } finally {
      delete Object.prototype[marker];
    }
  });

  // --- dotted-path deletion ----------------------------------------------------------
  function deletionCase(id, name, path) {
    add(id, name, function () {
      const marker = 'moutSecUnset' + (path.indexOf('__proto__') === -1 ? 'Ctor' : 'Proto');
      Object.defineProperty(Object.prototype, marker, {
        value: 'keep', writable: true, configurable: true, enumerable: false,
      });
      try {
        attempt(() => unset({}, path + '.' + marker));
        if (Object.prototype[marker] !== 'keep') {
          throw new Error(`${path} deleted ${marker} from Object.prototype`);
        }
      } finally {
        delete Object.prototype[marker];
      }
    });
  }

  deletionCase('unset-constructor-prototype', 'deleting a path cannot reach a shared prototype through constructor',
    'constructor.prototype');
  deletionCase('unset-proto-segment', 'deleting a path cannot reach a shared prototype through __proto__',
    '__proto__');

  return cases;
};
