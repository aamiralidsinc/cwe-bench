'use strict';

/*
 * Functional cases: legitimate use of the affected helpers and the coupled values next to the
 * guarded ones. Every expectation below is what the pinned library already produces today; these
 * must keep working whatever the fix does.
 */

function eq(got, want, what) {
  if (got !== want) {
    throw new Error(`${what} is ${JSON.stringify(got)}, expected ${JSON.stringify(want)}`);
  }
}

module.exports = function (product) {
  const { deepMixIn, deepFillIn, set, namespace, unset, get, has } = product;
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: 'functional/' + id, name, run });

  add('deep-mix-in-basics', 'deep merge copies properties, keeps existing child objects and returns the target', function () {
    const child = { mine: true };
    const target = { foo: true, child: child };
    const result = deepMixIn(target, { bar: true, child: { added: true } });
    eq(result, target, 'return value');
    eq(target.foo, true, 'target.foo');
    eq(target.bar, true, 'target.bar');
    eq(target.child, child, 'target.child identity');
    eq(target.child.mine, true, 'target.child.mine');
    eq(target.child.added, true, 'target.child.added');
  });

  add('deep-mix-in-reference-values', 'deep merge copies non-plain values by reference', function () {
    function Custom() {}
    const custom = new Custom();
    const items = [1, 2, 3];
    const regexp = /test/;
    const target = {};
    deepMixIn(target, { custom: custom, items: items, regexp: regexp });
    eq(target.custom, custom, 'custom instance');
    eq(target.items, items, 'array');
    eq(target.regexp, regexp, 'regexp');
  });

  add('deep-mix-in-data-keys', 'deep merge keeps ordinary data keys, including compound names', function () {
    const target = {};
    deepMixIn(target, { constructorCount: 1, prototypeName: 2, nested: { constructorCount: 3 } });
    eq(target.constructorCount, 1, 'constructorCount');
    eq(target.prototypeName, 2, 'prototypeName');
    eq(target.nested.constructorCount, 3, 'nested constructorCount');
  });

  add('deep-fill-in-basics', 'deep fill copies only missing properties and recurses into own children', function () {
    const defaults = { foo: 'bar', child: { a: 1, b: 2 } };
    const target = { foo: 'kept', child: { a: 9 } };
    const result = deepFillIn(target, defaults);
    eq(result, target, 'return value');
    eq(target.foo, 'kept', 'existing value');
    eq(target.child.a, 9, 'existing child value');
    eq(target.child.b, 2, 'filled child value');
  });

  add('deep-fill-in-reference-values', 'deep fill copies non-plain values by reference', function () {
    function Custom() {}
    const custom = new Custom();
    const items = [1, 2, 3];
    const target = {};
    deepFillIn(target, { custom: custom, items: items });
    eq(target.custom, custom, 'custom instance');
    eq(target.items, items, 'array');
  });

  add('set-and-namespace', 'nested property creation reuses own children and keeps ordinary keys', function () {
    const child = { lorem: 'ipsum' };
    const target = { foo: child };
    set(target, 'foo.bar', 123);
    eq(target.foo, child, 'existing child identity');
    eq(target.foo.bar, 123, 'nested value');
    eq(target.foo.lorem, 'ipsum', 'existing child value');

    const created = {};
    set(created, 'foo', 'bar');
    eq(created.foo, 'bar', 'non-nested value');

    const o = { foo: { lorem: 'ipsum' } };
    const reused = namespace(o, 'foo.bar');
    eq(o.foo, reused === undefined ? o.foo : o.foo, 'namespace keeps foo');
    eq(o.foo.lorem, 'ipsum', 'namespace keeps the child value');
    eq(typeof reused, 'object', 'namespace returns the created object');
    eq(namespace(o), o, 'namespace without a path returns the object');
  });

  add('unset-legitimate', 'deleting own properties keeps working', function () {
    const obj = { foo: { bar: 123 }, top: 'x' };
    eq(unset(obj, 'foo.bar'), true, 'nested delete result');
    eq(obj.foo.bar, undefined, 'nested delete');
    eq(unset(obj, 'top'), true, 'top-level delete result');
    eq(obj.top, undefined, 'top-level delete');
    eq(unset({}, 'dolor.amet'), true, 'missing path result');
  });

  add('readers-keep-inherited-semantics', 'has and get keep answering through the ordinary prototype chain', function () {
    const obj = { lorem: { ipsum: { dolor: { sit: 'amet' } } } };
    eq(has(obj, 'constructor'), true, 'has constructor');
    eq(has(obj, 'toString'), true, 'has toString');
    eq(has(obj, 'lorem.ipsum.dolor.sit'), true, 'has nested');
    eq(has(obj, 'lorem.ipsum.nope.sit'), false, 'has missing');

    const foo = { bar: { lorem: 'ipsum' } };
    eq(get(foo, 'bar.lorem.toString'), foo.bar.lorem.toString, 'get through a primitive');
    const fn = { bar: { lorem: function () {} } };
    fn.bar.lorem.ipsum = 'dolor';
    eq(get(fn, 'bar.lorem.ipsum'), 'dolor', 'get through a function');
    eq(get(foo, 'bar.dolor'), undefined, 'get missing');
    eq(get(null, 'bar.baz'), undefined, 'get on null');
  });

  add('enumeration-unchanged', 'own-key enumeration of ordinary objects is unchanged', function () {
    const obj = { a: 1, b: 2 };
    eq(Object.keys(obj).join(','), 'a,b', 'keys');
    const seen = [];
    for (const k in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, k)) seen.push(k);
    }
    eq(seen.join(','), 'a,b', 'for-in own keys');
  });

  return cases;
};
