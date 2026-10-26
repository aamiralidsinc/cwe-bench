'use strict';

/*
 * Control functional cases: legitimate use of the reported helper and the coupled values next to
 * the guarded one. Every expectation is what the pinned library already produces today.
 */

function eq(got, want, what) {
  if (got !== want) {
    throw new Error(`${what} is ${JSON.stringify(got)}, expected ${JSON.stringify(want)}`);
  }
}

module.exports = function (product) {
  const { deepMixIn } = product;
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: 'functional/' + id, name, run });

  add('mix-basics', 'deep merge copies properties and returns the target', function () {
    const target = { foo: true };
    const result = deepMixIn(target, { bar: true });
    eq(result, target, 'return value');
    eq(target.foo, true, 'target.foo');
    eq(target.bar, true, 'target.bar');
  });

  add('mix-child-objects', 'deep merge keeps existing child objects and mixes into them', function () {
    const child = { mine: true };
    const target = { child: child };
    deepMixIn(target, { child: { added: true } });
    eq(target.child, child, 'child identity');
    eq(target.child.mine, true, 'child.mine');
    eq(target.child.added, true, 'child.added');
  });

  add('mix-reference-values', 'deep merge copies non-plain values by reference', function () {
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

  add('mix-data-keys', 'deep merge keeps ordinary data keys, including compound names', function () {
    const target = {};
    deepMixIn(target, { constructorCount: 1, prototypeName: 2, nested: { constructorCount: 3 } });
    eq(target.constructorCount, 1, 'constructorCount');
    eq(target.prototypeName, 2, 'prototypeName');
    eq(target.nested.constructorCount, 3, 'nested constructorCount');
  });

  add('mix-multiple-sources', 'deep merge accepts several sources in order', function () {
    const target = {};
    deepMixIn(target, { a: 1 }, { b: 2 }, { a: 3 });
    eq(target.a, 3, 'later source wins');
    eq(target.b, 2, 'earlier source kept');
  });

  add('mix-overwrite-values', 'deep merge overwrites non-object values in the target', function () {
    const target = { foo: { a: true }, bar: [1, 2, 3] };
    deepMixIn(target, { foo: null, bar: 1 });
    eq(target.foo, null, 'null value');
    eq(target.bar, 1, 'scalar value');
  });

  return cases;
};
