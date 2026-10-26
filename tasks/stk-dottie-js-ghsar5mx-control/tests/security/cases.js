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

  return cases;
};
