'use strict';

/*
 * Security cases for the advisory's own routes: a classification check must
 * answer for the address the IPv6 value actually reaches. Every case drives the
 * library's public classes and expects a literal boolean; nothing is computed
 * with the product.
 */

function check(label, actual, expected) {
  if (actual !== expected) {
    throw new Error(`${label} is ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
  }
}

function v6Case(Address6, id, input, method, expected) {
  return {
    classname: 'security/' + id,
    name: `${id}: ${input}.${method}() is ${expected}`,
    run() {
      const address = new Address6(input);
      check(method, address[method](), expected);
    },
  };
}

module.exports = function ({ Address6 }) {
  const cases = [];
  const v6 = (...args) => cases.push(v6Case(Address6, ...args));

  // An IPv6 value that carries an IPv4 address reaches that IPv4 address.
  v6('S1-mapped-loopback', '::ffff:127.0.0.1', 'isLoopback', true);
  v6('S1-mapped-link-local', '::ffff:169.254.169.254', 'isLinkLocal', true);
  v6('S1-mapped-multicast', '::ffff:224.0.0.1', 'isMulticast', true);
  v6('S1-mapped-unspecified', '::ffff:0.0.0.0', 'isUnspecified', true);
  v6('S1-nat64-loopback', '64:ff9b::7f00:1', 'isLoopback', true);
  v6('S1-nat64-link-local', '64:ff9b::a9fe:a9fe', 'isLinkLocal', true);
  v6('S1-nat64-multicast', '64:ff9b::e000:1', 'isMulticast', true);
  v6('S1-nat64-unspecified', '64:ff9b::', 'isUnspecified', true);

  // The NAT64 local-use block is not publicly reachable as a whole.
  v6('S4-local-use-first', '64:ff9b:1::1', 'isPrivate', true);
  v6('S4-local-use-embedded-private', '64:ff9b:1:7f00:0:100::', 'isPrivate', true);
  v6('S4-local-use-high', '64:ff9b:1:ffff:ffff:ffff:ffff:1', 'isPrivate', true);
  // ... while globally reachable addresses stay public.
  v6('S4-nat64-public-is-public', '64:ff9b::808:808', 'isPrivate', false);
  v6('S4-global-is-public', '2001:4860:4860::8888', 'isPrivate', false);

  return cases;
};
