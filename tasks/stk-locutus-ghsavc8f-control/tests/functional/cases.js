'use strict';

/*
 * Functional cases: ordinary use keeps working exactly as it did. Expected values are literals
 * written here (taken from the library's documented examples); nothing is computed with the
 * product. These are also the coupled values that an over-broad refusal or a null-prototype
 * result would break.
 */

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

function canon(v) {
  if (Array.isArray(v)) return v.map(canon);
  if (v && typeof v === 'object') {
    const out = {};
    for (const k of Object.keys(v).sort()) out[k] = canon(v[k]);
    return out;
  }
  return v;
}

function eq(actual, expected, what) {
  const a = JSON.stringify(canon(actual));
  const e = JSON.stringify(canon(expected));
  assert(a === e, `${what}: got ${a}, expected ${e}`);
}

function makeCase(id, title, run) {
  return { classname: 'functional/' + id, name: id + ': ' + title, run };
}

module.exports = function (load) {
  const parse_str = load('strings/parse_str.js');
  const unserialize = load('var/unserialize.js');
  const ini_set = load('info/ini_set.js');
  const ini_get = load('info/ini_get.js');
  const array_merge = load('array/array_merge.js');
  const array_merge_recursive = load('array/array_merge_recursive.js');
  const array_replace = load('array/array_replace.js');
  const array_replace_recursive = load('array/array_replace_recursive.js');
  const array_change_key_case = load('array/array_change_key_case.js');
  const array_combine = load('array/array_combine.js');

  const cases = [];

  cases.push(makeCase('F-parse-basic', 'ordinary request string', function () {
    const out = {};
    parse_str('first=foo&second=bar', out);
    eq(out, { first: 'foo', second: 'bar' }, 'parse result');
  }));

  cases.push(makeCase('F-parse-normalisation', 'documented name normalisation', function () {
    const out = {};
    parse_str('user.name=1&str_a=Jack+and+Jill', out);
    eq(out, { user_name: '1', str_a: 'Jack and Jill' }, 'normalised result');
  }));

  cases.push(makeCase('F-parse-nested', 'nested and quoted names', function () {
    const out = { 3: 'a' };
    parse_str('a[b]["c"]=def&a[q]=t+5', out);
    eq(out, { 3: 'a', a: { b: { c: 'def' }, q: 't 5' } }, 'nested result');
  }));

  cases.push(makeCase('F-parse-append', 'a scalar followed by an appended array element', function () {
    const out = {};
    parse_str('a=1&a[]=2', out);
    eq(out, { a: { 0: '2' } }, 'append result');
  }));

  cases.push(makeCase('F-parse-array', 'automatically indexed array elements', function () {
    const out = {};
    parse_str('a[][]=value', out);
    eq(out, { a: { 0: { 0: 'value' } } }, 'array result');
  }));

  cases.push(makeCase('F-unserialize-object', 'associative serialized value', function () {
    const r = unserialize('a:2:{s:9:"firstName";s:5:"Kevin";s:7:"midName";s:3:"van";}', 'throw');
    eq(r, { firstName: 'Kevin', midName: 'van' }, 'deserialised object');
  }));

  cases.push(makeCase('F-unserialize-list', 'sequential serialized value', function () {
    const r = unserialize('a:3:{i:0;s:5:"Kevin";i:1;s:3:"van";i:2;s:9:"Zonneveld";}', 'throw');
    assert(Array.isArray(r), 'a sequentially indexed value must deserialise to a list');
    eq(r, ['Kevin', 'van', 'Zonneveld'], 'deserialised list');
  }));

  cases.push(makeCase('F-unserialize-stdclass', 'serialized object value', function () {
    const r = unserialize('O:8:"stdClass":1:{s:3:"foo";b:1;}', 'throw');
    eq(r, { foo: true }, 'deserialised object value');
  }));

  cases.push(makeCase('F-ini-set-get', 'ordinary setting round trip', function () {
    const previous = global.$locutus;
    try {
      global.$locutus = undefined;
      assert(ini_set('date.timezone', 'Asia/Hong_Kong') === undefined, 'the first set reports no previous value');
      assert(ini_get('date.timezone') === 'Asia/Hong_Kong', 'the stored value is readable');
      assert(ini_set('date.timezone', 'America/Chicago') === 'Asia/Hong_Kong', 'the second set reports the previous value');
      assert(ini_get('date.timezone') === 'America/Chicago', 'the replaced value is readable');
      ini_set('display_errors', 'On');
      assert(ini_get('display_errors') === 'on', 'a boolean-like setting keeps its normalised spelling');
    } finally {
      global.$locutus = previous;
    }
  }));

  cases.push(makeCase('F-array-merge', 'merge of associative arrays renumbers numeric keys', function () {
    eq(array_merge({ color: 'red', 0: 2, 1: 4 }, { 0: 'a', 1: 'b', color: 'green', shape: 'trapezoid', 2: 4 }),
      { color: 'green', 0: 2, 1: 4, 2: 'a', 3: 'b', shape: 'trapezoid', 4: 4 }, 'merge result');
  }));

  cases.push(makeCase('F-array-merge-lists', 'merge of plain lists concatenates', function () {
    eq(array_merge([1, 2], [3, 4]), [1, 2, 3, 4], 'list merge result');
  }));

  cases.push(makeCase('F-array-merge-recursive', 'recursive merge keeps the documented shape', function () {
    eq(array_merge_recursive({ color: { favorite: 'red' }, 0: 5 }, { 0: 10, color: { favorite: 'green', 0: 'blue' } }),
      { color: { favorite: ['red', 'green'], 0: 'blue' }, 0: 5, 1: 10 }, 'recursive merge result');
  }));

  cases.push(makeCase('F-array-replace', 'replace keeps the documented shape', function () {
    eq(array_replace(['orange', 'banana', 'apple', 'raspberry'], { 0: 'pineapple', 4: 'cherry' }, { 0: 'grape' }),
      { 0: 'grape', 1: 'banana', 2: 'apple', 3: 'raspberry', 4: 'cherry' }, 'replace result');
  }));

  cases.push(makeCase('F-array-replace-recursive', 'recursive replace keeps the documented shape', function () {
    eq(array_replace_recursive({ citrus: ['orange'], berries: ['blackberry', 'raspberry'] },
      { citrus: ['pineapple'], berries: ['blueberry'] }),
      { citrus: ['pineapple'], berries: ['blueberry', 'raspberry'] }, 'recursive replace result');
  }));

  cases.push(makeCase('F-array-change-key-case', 'key case change keeps ordinary values', function () {
    eq(array_change_key_case({ FuBaR: 42 }, 'CASE_LOWER'), { fubar: 42 }, 'lower-case result');
    eq(array_change_key_case({ FuBaR: 42 }, 'CASE_UPPER'), { FUBAR: 42 }, 'upper-case result');
    const list = [3, 5];
    assert(array_change_key_case(list) === list, 'a plain list is returned unchanged');
  }));

  cases.push(makeCase('F-array-combine', 'combine keeps ordinary keys and values', function () {
    eq(array_combine([0, 1, 2], ['kevin', 'van', 'zonneveld']),
      { 0: 'kevin', 1: 'van', 2: 'zonneveld' }, 'combine result');
  }));

  cases.push(makeCase('F-ordinary-prototypes', 'ordinary results keep their normal prototype', function () {
    assert(Object.getPrototypeOf(array_merge({ a: 1 }, { b: 2 })) === Object.prototype,
      'a merged associative result must be an ordinary object');
    assert(Object.getPrototypeOf(array_replace({ a: 1 }, { b: 2 })) === Object.prototype,
      'a replaced associative result must be an ordinary object');
    const r = unserialize('a:1:{s:3:"foo";b:1;}', 'throw');
    assert(Object.getPrototypeOf(r) === Object.prototype, 'a deserialised associative value must be an ordinary object');
  }));

  return cases;
};
