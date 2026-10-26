'use strict';

/*
 * Security cases: a caller- or payload-supplied name must never change the prototype of any
 * object or add a property to an object outside the call. Every case drives an exported library
 * function directly, uses harmless marker values, and asserts the protected outcome (no shared or
 * inherited property appeared), never a particular refusal style.
 */

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

function hasOwn(obj, key) {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

function clean(names) {
  for (const n of names) {
    try { delete Object.prototype[n]; } catch (_) { /* ignore */ }
    try { delete Object[n]; } catch (_) { /* ignore */ }
  }
}

function callIgnoringError(fn) {
  try { fn(); } catch (_) { /* a refusal may be reported as an error */ }
}

function makeCase(id, title, run) {
  return { classname: 'security/' + id, name: id + ': ' + title, run };
}

module.exports = function (load) {
  const parse_str = load('strings/parse_str.js');
  const unserialize = load('var/unserialize.js');
  const ini_set = load('info/ini_set.js');
  const array_merge = load('array/array_merge.js');
  const array_merge_recursive = load('array/array_merge_recursive.js');
  const array_replace = load('array/array_replace.js');
  const array_replace_recursive = load('array/array_replace_recursive.js');
  const array_change_key_case = load('array/array_change_key_case.js');
  const array_combine = load('array/array_combine.js');

  const cases = [];

  // ------------------------------------------------------------------ caller-supplied names in
  // request strings. The process has already loaded code that replaced built-in helpers; the
  // library's protection must not rest on a method that can be replaced under it.
  function parseCase(id, tamper, payload) {
    const marker = 't1_' + id.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    cases.push(makeCase(id, `request string ${JSON.stringify(payload(marker))} cannot reach Object.prototype`, function () {
      clean([marker]);
      const originalIncludes = String.prototype.includes;
      const originalTest = RegExp.prototype.test;
      try {
        if (tamper.includes) String.prototype.includes = function () { return false; };
        if (tamper.regex) RegExp.prototype.test = function () { return false; };
        callIgnoringError(function () { parse_str(payload(marker), {}); });
      } finally {
        String.prototype.includes = originalIncludes;
        RegExp.prototype.test = originalTest;
      }
      try {
        assert(!hasOwn(Object.prototype, marker),
          `parsing ${JSON.stringify(payload(marker))} added ${marker} to Object.prototype`);
        assert(({})[marker] === undefined,
          `plain objects inherited ${marker} after parsing ${JSON.stringify(payload(marker))}`);
      } finally {
        clean([marker]);
      }
    }));
  }

  parseCase('T1-includes-proto', { includes: true }, m => `__proto__[${m}]=yes`);
  parseCase('T1-includes-constructor', { includes: true }, m => `constructor[prototype][${m}]=yes`);
  parseCase('T1-includes-nested', { includes: true }, m => `a[__proto__][${m}]=yes`);
  parseCase('T1-both-proto', { includes: true, regex: true }, m => `__proto__[${m}]=yes`);
  parseCase('T1-both-constructor', { includes: true, regex: true }, m => `constructor[prototype][${m}]=yes`);

  // ------------------------------------------------------------------ values rebuilt from a
  // payload. A prototype-named key must not become the prototype of the rebuilt structure.
  function unserializeCase(id, payload, check) {
    cases.push(makeCase(id, `payload key cannot become a prototype (${id})`, function () {
      clean(['isAdmin']);
      let result;
      let refused = false;
      try {
        result = unserialize(payload, 'throw');
      } catch (_) {
        refused = true;
      }
      try {
        assert(!hasOwn(Object.prototype, 'isAdmin'),
          'deserialising the payload added isAdmin to Object.prototype, shared with every object');
        if (!refused) check(result);
      } finally {
        clean(['isAdmin']);
      }
    }));
  }

  unserializeCase(
    'T2-array-proto',
    'a:2:{s:9:"__proto__";a:1:{s:7:"isAdmin";b:1;}s:4:"name";s:3:"bob";}',
    function (r) {
      assert(r && r.name === 'bob', 'an ordinary key next to the prototype-named key must be preserved');
      assert(Object.getPrototypeOf(r) === Object.prototype,
        'the rebuilt object did not keep Object.prototype as its prototype');
      assert(r.isAdmin === undefined, 'the payload value became an inherited property (isAdmin)');
    });

  unserializeCase(
    'T2-object-proto',
    'O:8:"stdClass":2:{s:9:"__proto__";a:1:{s:7:"isAdmin";b:1;}s:4:"name";s:3:"bob";}',
    function (r) {
      assert(r && r.name === 'bob', 'an ordinary key next to the prototype-named key must be preserved');
      assert(Object.getPrototypeOf(r) === Object.prototype,
        'the rebuilt object did not keep Object.prototype as its prototype');
      assert(r.isAdmin === undefined, 'the payload value became an inherited property (isAdmin)');
    });

  unserializeCase(
    'T2-object-under-array',
    'a:1:{i:0;O:8:"stdClass":1:{s:9:"__proto__";a:1:{s:7:"isAdmin";b:1;}}}',
    function (r) {
      assert(Array.isArray(r) && r.length === 1, 'the ordinary list structure must be preserved');
      assert(Object.getPrototypeOf(r[0]) === Object.prototype,
        'the nested rebuilt object did not keep Object.prototype as its prototype');
      assert(r[0].isAdmin === undefined, 'the nested payload value became an inherited property');
    });

  unserializeCase(
    'T2-array-under-object',
    'O:8:"stdClass":1:{s:1:"k";a:1:{s:9:"__proto__";a:1:{s:7:"isAdmin";b:1;}}}',
    function (r) {
      assert(r && r.k && typeof r.k === 'object', 'the ordinary nested key must be preserved');
      assert(Object.getPrototypeOf(r.k) === Object.prototype,
        'the nested rebuilt structure did not keep Object.prototype as its prototype');
      assert(r.k.isAdmin === undefined, 'the nested payload value became an inherited property');
    });

  // ------------------------------------------------------------------ a caller-chosen name used
  // as a setting. It must never resolve to a built-in object and be written there.
  function iniCase(id, varname) {
    cases.push(makeCase(id, `setting name ${JSON.stringify(varname)} cannot write a shared built-in`, function () {
      const previous = global.$locutus;
      clean(['local_value']);
      try {
        global.$locutus = undefined;
        callIgnoringError(function () { ini_set(varname, 't3value'); });
        assert(!hasOwn(Object.prototype, 'local_value'),
          'setting the name wrote local_value to Object.prototype, shared with every object');
        assert(!hasOwn(Object, 'local_value'),
          'setting the name wrote local_value to a shared built-in object');
        assert(({})['local_value'] === undefined, 'plain objects inherited local_value after the call');
      } finally {
        global.$locutus = previous;
        clean(['local_value']);
      }
    }));
  }

  iniCase('T3-proto-name', '__proto__');
  iniCase('T3-constructor-name', 'constructor');

  // ------------------------------------------------------------------ caller keys copied into a
  // result. A prototype-named key must stay out of the prototype.
  function arrayCase(id, fn, check) {
    cases.push(makeCase(id, `caller key cannot change the prototype of the result (${id})`, function () {
      clean(['isAdmin']);
      let result;
      let refused = false;
      try {
        result = fn();
      } catch (_) {
        refused = true;
      }
      try {
        assert(!hasOwn(Object.prototype, 'isAdmin'),
          'the call added isAdmin to Object.prototype, shared with every object');
        if (!refused) {
          assert(Object.getPrototypeOf(result) === Object.prototype,
            'the returned object did not keep Object.prototype as its prototype');
          assert(result.isAdmin === undefined, 'the caller-supplied value became an inherited property');
          if (check) check(result);
        }
      } finally {
        clean(['isAdmin']);
      }
    }));
  }

  function withProtoKey() {
    return JSON.parse('{"__proto__":{"isAdmin":true},"x":1}');
  }

  arrayCase('T4-merge', () => array_merge(withProtoKey(), { y: 2 }), function (r) {
    assert(r.x === 1, 'an ordinary key must be preserved');
    assert(r.y === 2, 'a key from another argument must be preserved');
  });
  arrayCase('T4-merge-recursive', () => array_merge_recursive(withProtoKey(), { y: 2 }), function (r) {
    assert(r.x === 1, 'an ordinary key must be preserved');
    assert(r.y === 2, 'a key from another argument must be preserved');
  });
  arrayCase('T4-replace', () => array_replace(withProtoKey(), { y: 2 }), function (r) {
    assert(r.x === 1, 'an ordinary key must be preserved');
    assert(r.y === 2, 'a replacing key must be preserved');
  });
  arrayCase('T4-replace-recursive', () => array_replace_recursive(withProtoKey(), { y: 2 }), function (r) {
    assert(r.x === 1, 'an ordinary key must be preserved');
    assert(r.y === 2, 'a replacing key must be preserved');
  });
  arrayCase('T4-change-key-case', () => array_change_key_case(withProtoKey()), function (r) {
    assert(r.x === 1, 'an ordinary key must be preserved');
  });
  arrayCase('T4-combine', () => array_combine(['__proto__', 'name'], [{ isAdmin: true }, 'bob']), function (r) {
    assert(r.name === 'bob', 'an ordinary key/value pair must be preserved');
  });

  return cases;
};
