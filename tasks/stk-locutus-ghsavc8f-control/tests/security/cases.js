'use strict';

/*
 * Security cases (control task): the reported request-string route only. A caller-supplied name
 * must never change the prototype of any object while the process's built-in helpers have been
 * replaced. Every case drives the exported function directly and asserts the protected outcome.
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
  const cases = [];

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

  return cases;
};
