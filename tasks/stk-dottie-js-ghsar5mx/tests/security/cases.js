'use strict';

/*
 * Security cases: a caller-supplied path, key or path part must never make the library write a
 * value onto a prototype object. Every case drives a public entry point, then checks the outcome
 * only: the objects the library built keep an ordinary prototype, the attacker's field is not
 * visible through inheritance, and the language's shared prototype is untouched. A refusal that
 * raises an error is acceptable; a refusal that writes nothing is acceptable; the error mode is
 * not judged. Expected names are literals written here; nothing is computed with the product.
 */

function own(obj, key) {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

function checkProtected(observations, marker, id) {
  for (const obs of observations) {
    const obj = obs.obj;
    if (obj === undefined || obj === null || typeof obj !== 'object') continue;
    const proto = Object.getPrototypeOf(obj);
    // An ordinary object or a deliberately prototype-less container is fine; anything else means
    // the caller's name replaced this object's prototype with an object of its choosing.
    if (proto !== Object.prototype && proto !== null) {
      throw new Error(`${id}: ${obs.label} had its prototype replaced with a caller-influenced object`);
    }
    if (!own(obj, marker) && obj[marker] !== undefined) {
      throw new Error(`${id}: ${obs.label} exposes ${JSON.stringify(marker)} through inheritance`);
    }
  }
  if (({})[marker] !== undefined) {
    throw new Error(`${id}: the shared prototype of ordinary objects was modified`);
  }
}

module.exports = function (D) {
  const cases = [];

  function securityCase(id, description, call, observe) {
    const marker = 'probe_' + id.replace(/[^A-Za-z0-9]+/g, '_');
    cases.push({
      classname: 'security/' + id,
      name: `${id}: ${description}`,
      run() {
        const target = {};
        let result;
        try {
          result = call(D, target, marker);
        } catch (e) {
          // Any refusal shape is acceptable; only side effects are judged below.
        }
        checkProtected(observe(D, target, marker, result), marker, id);
      },
    });
  }

  // --- A path written as a string, with a prototype-bearing segment at each position ---
  securityCase('T1-set-first', 'a first path segment naming a prototype is not written',
    (D, t, m) => D.set(t, '__proto__.' + m, true),
    (D, t) => [{ label: 'target', obj: t }]);

  securityCase('T1-set-second', 'a second path segment naming a prototype is not written',
    (D, t, m) => D.set(t, 'session.__proto__.' + m, true),
    (D, t) => [{ label: 'target', obj: t }, { label: 'session', obj: t.session }]);

  securityCase('T1-set-third', 'a third path segment naming a prototype is not written',
    (D, t, m) => D.set(t, 'a.b.__proto__.' + m, true),
    (D, t) => [{ label: 'target', obj: t }, { label: 'a.b', obj: t.a && t.a.b }]);

  securityCase('T1-set-last', 'a final path segment naming a prototype is not written',
    (D, t, m) => D.set(t, 'session.__proto__', { [m]: true }),
    (D, t) => [{ label: 'target', obj: t }, { label: 'session', obj: t.session }]);

  securityCase('T1-set-force', 'the force option does not open a prototype-bearing segment',
    (D, t, m) => { t.session = null; D.set(t, 'session.__proto__.' + m, true, { force: true }); },
    (D, t) => [{ label: 'target', obj: t }, { label: 'session', obj: t.session }]);

  securityCase('T1-default-route', 'the default route does not write through a prototype-bearing segment',
    (D, t, m) => D['default'](t, 'session.__proto__.' + m, true),
    (D, t) => [{ label: 'target', obj: t }, { label: 'session', obj: t.session }]);

  // --- A path written as an array whose parts are not all strings ---
  securityCase('T5-array-json', 'a path part parsed from JSON that names a prototype is not written',
    (D, t, m) => {
      const path = JSON.parse('{"parts":[["__proto__"],"' + m + '"]}').parts;
      D.set(t, path, true);
    },
    (D, t) => [{ label: 'target', obj: t }]);

  securityCase('T5-array-middle', 'a non-string middle path part naming a prototype is not written',
    (D, t, m) => D.set(t, ['session', ['__proto__'], m], true),
    (D, t) => [{ label: 'target', obj: t }, { label: 'session', obj: t.session }]);

  securityCase('T5-array-last', 'a non-string final path part naming a prototype is not written',
    (D, t, m) => D.set(t, [['__proto__']], { [m]: true }),
    (D, t) => [{ label: 'target', obj: t }]);

  securityCase('T5-array-converted', 'a path part whose text is a prototype name is not written',
    (D, t, m) => D.set(t, [{ toString: function () { return '__proto__'; } }, m], true),
    (D, t) => [{ label: 'target', obj: t }]);

  securityCase('T5-default-array', 'the default route is closed for non-string path parts too',
    (D, t, m) => D['default'](t, [['__proto__'], m], true),
    (D, t) => [{ label: 'target', obj: t }]);

  // --- A key written with the separator, through the flat-object conversion ---
  securityCase('T3-transform-first', 'a converted key beginning with a prototype name is not written',
    (D, t, m) => D.transform({ ['__proto__.' + m]: true }),
    (D, t, m, r) => [{ label: 'result', obj: r }]);

  securityCase('T3-transform-second', 'a converted key with a second prototype-bearing part is not written',
    (D, t, m) => D.transform({ ['user.__proto__.' + m]: true, 'user.name': 'guest' }),
    (D, t, m, r) => [{ label: 'result', obj: r }, { label: 'user', obj: r && r.user }]);

  securityCase('T3-transform-third', 'a converted key with a third prototype-bearing part is not written',
    (D, t, m) => D.transform({ ['a.b.__proto__.' + m]: true }),
    (D, t, m, r) => [{ label: 'result', obj: r },
                     { label: 'a.b', obj: r && r.a && r.a.b }]);

  securityCase('T3-transform-last', 'a converted key ending with a prototype name is not written',
    (D, t, m) => D.transform({ 'user.__proto__': { [m]: true } }),
    (D, t, m, r) => [{ label: 'result', obj: r }, { label: 'user', obj: r && r.user }]);

  securityCase('T3-transform-delimiter', 'a custom separator does not open a prototype-bearing part',
    (D, t, m) => D.transform({ ['user/__proto__/' + m]: true }, { delimiter: '/' }),
    (D, t, m, r) => [{ label: 'result', obj: r }, { label: 'user', obj: r && r.user }]);

  securityCase('T3-constructor-entry', 'the one-argument conversion call is closed too',
    (D, t, m) => D({ ['user.__proto__.' + m]: true }),
    (D, t, m, r) => [{ label: 'result', obj: r }, { label: 'user', obj: r && r.user }]);

  // --- A key written without the separator, through the flat-object conversion ---
  securityCase('T4-transform-plain-json', 'a lone prototype key parsed from JSON is not written',
    (D, t, m) => D.transform(JSON.parse('{"__proto__":{"' + m + '":true}}')),
    (D, t, m, r) => [{ label: 'result', obj: r }]);

  securityCase('T4-transform-plain-array', 'a lone prototype key inside an array input is not written',
    (D, t, m) => D.transform([JSON.parse('{"__proto__":{"' + m + '":true}}')]),
    (D, t, m, r) => [{ label: 'result[0]', obj: r && r[0] }]);

  securityCase('T4-transform-plain-sibling', 'a lone prototype key next to a legitimate key is not written',
    (D, t, m) => D.transform(JSON.parse('{"__proto__":{"' + m + '":true},"user.name":"guest"}')),
    (D, t, m, r) => [{ label: 'result', obj: r }, { label: 'user', obj: r && r.user }]);

  securityCase('T4-constructor-plain-json', 'the one-argument conversion call is closed for a lone prototype key',
    (D, t, m) => D(JSON.parse('{"__proto__":{"' + m + '":true}}')),
    (D, t, m, r) => [{ label: 'result', obj: r }]);

  return cases;
};
