'use strict';

/*
 * Functional cases: legitimate use and the coupled values that sit next to the hidden ones.
 * Every expectation below is what the pinned library already produces today (checked when the
 * task was built); these must keep working whatever the fix does. Values are literals in the
 * case table; nothing is computed with the product.
 */

function own(obj, key) {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

module.exports = function (D) {
  const cases = [];

  function functionalCase(id, description, run) {
    cases.push({
      classname: 'functional/' + id,
      name: `${id}: ${description}`,
      run,
    });
  }

  function eq(got, want, what) {
    if (got !== want) {
      throw new Error(`${what} is ${JSON.stringify(got)}, expected ${JSON.stringify(want)}`);
    }
  }

  // --- ordinary writes ---
  functionalCase('F-set-existing', 'setting an existing nested value keeps working', () => {
    const data = { foo: { bar: 'baa' } };
    D.set(data, 'foo.bar', 'baz');
    eq(data.foo.bar, 'baz', 'data.foo.bar');
  });

  functionalCase('F-set-create', 'writing a missing nested value still creates the structure', () => {
    const data = {};
    D.set(data, 'level1.level2', 'foo');
    eq(typeof data.level1, 'object', 'typeof data.level1');
    eq(data.level1.level2, 'foo', 'data.level1.level2');
  });

  functionalCase('F-set-undefined', 'an undefined intermediate value is still converted to an object', () => {
    const data = { values: undefined };
    D.set(data, 'values.level1', 'foo');
    eq(data.values.level1, 'foo', 'data.values.level1');
  });

  functionalCase('F-set-force-null', 'the force option still overwrites a null intermediate value', () => {
    const data = { values: null };
    D.set(data, 'values.level1', 'foo', { force: true });
    eq(data.values.level1, 'foo', 'data.values.level1');
  });

  functionalCase('F-set-force-nonobject', 'the force option still overwrites a non-object intermediate value', () => {
    const data = { foo: { bar: 'baa' } };
    D.set(data, 'foo.bar.baz', 'someValue', { force: true });
    eq(data.foo.bar.baz, 'someValue', 'data.foo.bar.baz');
  });

  functionalCase('F-set-throws-nonobject', 'an unsuitable intermediate value still raises without force', () => {
    const data = { foo: { bar: 'baa' } };
    let threw = false;
    try { D.set(data, 'foo.bar.baz', 'someValue'); } catch (e) { threw = true; }
    eq(threw, true, 'the error raised for a non-object intermediate value');
  });

  functionalCase('F-set-similar-names', 'a path part resembling a prototype name still binds', () => {
    const data = {};
    D.set(data, 'a.__proto__x.y', 1);
    eq(data.a && own(data.a, '__proto__x') ? data.a['__proto__x'].y : undefined, 1,
      'data.a["__proto__x"].y');
  });

  // --- array paths, including the coupled shapes next to the hidden ones ---
  functionalCase('F-set-array-dotted', 'an array path part that contains the separator stays whole', () => {
    const data = {};
    D.set(data, ['some.dot.containing', 'value'], 'razzamataz');
    eq(data['some.dot.containing'].value, 'razzamataz', 'data["some.dot.containing"].value');
  });

  functionalCase('F-set-array-nested', 'a non-string path part that names an ordinary key still binds', () => {
    const data = {};
    D.set(data, [['a.b'], 'value'], 7);
    eq(data['a.b'].value, 7, 'data["a.b"].value');
  });

  functionalCase('F-set-array-from-json', 'a path parsed from JSON still binds ordinary names', () => {
    const path = JSON.parse('{"parts":[["a.b"],"value"]}').parts;
    const data = {};
    D.set(data, path, 'ok');
    eq(data['a.b'].value, 'ok', 'data["a.b"].value');
  });

  // --- ordinary conversion ---
  functionalCase('F-transform-basic', 'dotted keys are still nested', () => {
    const r = D.transform({
      'user.name': 'John Doe',
      'user.email': 'jd@foobar.com',
      'user.location.country': 'Zanzibar',
      'user.location.city': 'Zanzibar City',
    });
    eq(r.user.name, 'John Doe', 'r.user.name');
    eq(r.user.email, 'jd@foobar.com', 'r.user.email');
    eq(r.user.location.city, 'Zanzibar City', 'r.user.location.city');
  });

  functionalCase('F-transform-delimiter', 'a custom separator still nests', () => {
    const r = D.transform({
      user_name: 'Mick Hansen',
      user_email: 'maker@mhansen.io',
      project_title: 'dottie',
    }, { delimiter: '_' });
    eq(r.user.name, 'Mick Hansen', 'r.user.name');
    eq(r.user.email, 'maker@mhansen.io', 'r.user.email');
    eq(r.project.title, 'dottie', 'r.project.title');
  });

  functionalCase('F-transform-null-break', 'a null intermediate value still stops that key', () => {
    const r = D.transform({
      'section.id': 20,
      'section.layout': null,
      'section.layout.id': null,
      'section.layout.name': null,
    });
    eq(r.section.layout, null, 'r.section.layout');
    eq(r['section.layout.id'], undefined, 'r["section.layout.id"]');
    eq(r['section.layout.name'], undefined, 'r["section.layout.name"]');
  });

  functionalCase('F-transform-array', 'array input is still converted element by element', () => {
    const r = D.transform([
      { 'customer.name': 'John Doe', 'customer.age': 15, client: 'Lolcat' },
      { 'client.name': 'John Doe', 'client.age': 15, customer: 'Lolcat' },
    ]);
    eq(r[0].customer.name, 'John Doe', 'r[0].customer.name');
    eq(r[1].client.name, 'John Doe', 'r[1].client.name');
  });

  functionalCase('F-transform-plain-key', 'a key without the separator is still an own field', () => {
    const r = D.transform({ 'customer.name': 'John Doe', client: 'Lolcat' });
    eq(r.client, 'Lolcat', 'r.client');
    eq(own(r, 'client'), true, 'client being an own field');
  });

  functionalCase('F-transform-similar-names', 'names that merely resemble a prototype name still bind', () => {
    const r = D.transform({ '__proto__x': 'safe', proto_field: 'ok', 'a.__proto__x': 'ok2' });
    eq(own(r, '__proto__x') ? r['__proto__x'] : undefined, 'safe', 'r["__proto__x"]');
    eq(own(r, 'proto_field') ? r.proto_field : undefined, 'ok', 'r.proto_field');
    eq(r.a && own(r.a, '__proto__x') ? r.a['__proto__x'] : undefined, 'ok2', 'r.a["__proto__x"]');
  });

  functionalCase('F-one-argument-entry', 'the one-argument conversion call still nests ordinary keys', () => {
    const r = D({ 'user.name': 'guest', 'user.role': 'reader' });
    eq(r.user.name, 'guest', 'r.user.name');
    eq(r.user.role, 'reader', 'r.user.role');
  });

  // --- reads and the default route ---
  functionalCase('F-get', 'reading nested values is unchanged', () => {
    const data = { a: { b: 1 }, 'c.d': { e: 2 } };
    eq(D.get(data, 'a.b'), 1, 'D.get(data, "a.b")');
    eq(D.get(data, ['c.d', 'e']), 2, 'D.get(data, ["c.d","e"])');
    eq(D.get(data, 'a.missing', 'fallback'), 'fallback', 'the default value');
  });

  functionalCase('F-default-route', 'the default route still writes only a missing value', () => {
    const data = { a: { b: 1 } };
    D['default'](data, 'a.b', 2);
    D['default'](data, 'a.c', 3);
    eq(data.a.b, 1, 'data.a.b');
    eq(data.a.c, 3, 'data.a.c');
  });

  return cases;
};
