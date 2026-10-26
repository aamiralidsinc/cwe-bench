'use strict';

/*
 * Security cases: a classification check must answer for the address the IPv6
 * value actually reaches. Every case drives the library's public classes and
 * expects a literal boolean; nothing is computed with the product.
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

function v4Case(Address4, id, input, method, expected) {
  return {
    classname: 'security/' + id,
    name: `${id}: ${input}.${method}() is ${expected}`,
    run() {
      const address = new Address4(input);
      check(method, address[method](), expected);
    },
  };
}

module.exports = function ({ Address4, Address6 }) {
  const cases = [];
  const v6 = (...args) => cases.push(v6Case(Address6, ...args));
  const v4 = (...args) => cases.push(v4Case(Address4, ...args));

  // An IPv6 value that carries an IPv4 address reaches that IPv4 address.
  v6('S1-mapped-loopback', '::ffff:127.0.0.1', 'isLoopback', true);
  v6('S1-mapped-link-local', '::ffff:169.254.169.254', 'isLinkLocal', true);
  v6('S1-mapped-multicast', '::ffff:224.0.0.1', 'isMulticast', true);
  v6('S1-mapped-unspecified', '::ffff:0.0.0.0', 'isUnspecified', true);
  v6('S1-nat64-loopback', '64:ff9b::7f00:1', 'isLoopback', true);
  v6('S1-nat64-link-local', '64:ff9b::a9fe:a9fe', 'isLinkLocal', true);
  v6('S1-nat64-multicast', '64:ff9b::e000:1', 'isMulticast', true);
  v6('S1-nat64-unspecified', '64:ff9b::', 'isUnspecified', true);

  // Link-local classification covers the whole link-local block.
  v6('S2-link-local-subnet-host', 'fe80:0:0:1::1', 'isLinkLocal', true);
  v6('S2-link-local-block-end', 'febf::1', 'isLinkLocal', true);
  v6('S2-link-local-block-mid', 'fea0::1', 'isLinkLocal', true);
  v6('S2-link-local-block-full', 'febf:1:2:3:4:5:6:7', 'isLinkLocal', true);

  // A host address is classified by its own bits, whatever prefix it carries.
  v4('S3-v4-private-short-prefix', '10.1.2.3/4', 'isPrivate', true);
  v4('S3-v4-link-local-short-prefix', '169.254.1.1/8', 'isLinkLocal', true);
  v4('S3-v4-loopback-zero-prefix', '127.0.0.1/0', 'isLoopback', true);
  v4('S3-v4-broadcast-short-prefix', '255.255.255.255/24', 'isBroadcast', true);
  v4('S3-v4-cgnat-short-prefix', '100.64.0.1/8', 'isCGNAT', true);
  v4('S3-v4-unspecified-zero-prefix', '0.0.0.0/0', 'isUnspecified', true);
  v6('S3-v6-ula-short-prefix', 'fc00::1/4', 'isULA', true);
  v6('S3-v6-documentation-short-prefix', '2001:db8::1/16', 'isDocumentation', true);

  // The NAT64 local-use block is not publicly reachable as a whole.
  v6('S4-local-use-first', '64:ff9b:1::1', 'isPrivate', true);
  v6('S4-local-use-embedded-private', '64:ff9b:1:7f00:0:100::', 'isPrivate', true);
  v6('S4-local-use-high', '64:ff9b:1:ffff:ffff:ffff:ffff:1', 'isPrivate', true);
  // ... while globally reachable addresses stay public.
  v6('S4-nat64-public-is-public', '64:ff9b::808:808', 'isPrivate', false);
  v6('S4-global-is-public', '2001:4860:4860::8888', 'isPrivate', false);

  return cases;
};
