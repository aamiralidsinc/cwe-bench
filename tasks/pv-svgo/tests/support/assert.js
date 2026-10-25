'use strict';

// Minimal assertion helpers. Tests compute their own expectations; nothing here calls product code.
function fail(message) {
  throw new Error(message);
}

exports.ok = (value, message) => {
  if (!value) fail(message || 'expected a truthy value');
};

exports.equal = (actual, expected, message) => {
  if (actual !== expected) {
    fail(
      (message || 'values differ') +
        `: ${JSON.stringify(actual)} !== ${JSON.stringify(expected)}`,
    );
  }
};

exports.includes = (haystack, needle, message) => {
  if (typeof haystack !== 'string' || !haystack.includes(needle)) {
    fail((message || 'missing text') + `: ${JSON.stringify(needle)} in ${JSON.stringify(haystack)}`);
  }
};

exports.notMatch = (text, pattern, message) => {
  if (pattern.test(text)) {
    fail((message || 'unexpected match') + `: ${pattern} in ${JSON.stringify(text)}`);
  }
};

exports.match = (text, pattern, message) => {
  if (!pattern.test(text)) {
    fail((message || 'expected match') + `: ${pattern} in ${JSON.stringify(text)}`);
  }
};
