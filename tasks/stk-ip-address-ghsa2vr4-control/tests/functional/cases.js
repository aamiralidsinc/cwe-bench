'use strict';

/*
 * Functional cases: legitimate use and the values coupled to the classification
 * fixes. Every expectation below is what the pinned library already produces
 * today, or a documented public contract of the product. Nothing is computed
 * with the product.
 */

function check(label, actual, expected) {
  if (actual !== expected) {
    throw new Error(`${label} is ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
  }
}

module.exports = function ({ Address4, Address6 }) {
  const cases = [];
  const add = (id, fn) => cases.push({ classname: 'functional/' + id, name: id, run: fn });

  // Subnet containment keeps its network meaning: a wider network is not
  // inside a narrower one, and a host inside a range is inside it.
  add('F-subnet-v6-host-inside', () => {
    check('isInSubnet', new Address6('2001:db8::1/64').isInSubnet(new Address6('2001:db8::/32')), true);
  });
  add('F-subnet-v6-wider-not-inside', () => {
    check('isInSubnet', new Address6('2001:db8::/32').isInSubnet(new Address6('2001:db8::/48')), false);
  });
  add('F-subnet-v4-wider-not-inside', () => {
    check('isInSubnet', new Address4('10.0.0.0/8').isInSubnet(new Address4('10.0.0.0/16')), false);
  });
  add('F-subnet-v4-host-inside', () => {
    check('isInSubnet', new Address4('192.168.1.5/24').isInSubnet(new Address4('192.168.0.0/16')), true);
  });

  // Scope and type results the library already returns.
  add('F-scope-existing-values', () => {
    check('scope-ula', new Address6('fd12:3456:789a::1').getScope(), 'Global');
    check('scope-documentation', new Address6('2001:db8::1').getScope(), 'Global');
    check('scope-six-to-four', new Address6('2002:c0a8:1::').getScope(), 'Global');
    check('scope-link-local', new Address6('fe80::2ff:33ff:feaa:bbcc').getScope(), 'Link local');
    check('scope-loopback', new Address6('::1').getScope(), 'Link local');
    check('scope-unspecified', new Address6('::').getScope(), 'Unknown');
    check('scope-multicast-link', new Address6('ff02::1').getScope(), 'Link local');
    check('scope-multicast-global', new Address6('ff0e::1').getScope(), 'Global');
  });
  add('F-type-existing-values', () => {
    check('type-ula', new Address6('fc00::').getType(), 'Unique local');
    check('type-six-to-four', new Address6('2002:c0a8:1::').getType(), '6to4');
    check('type-documentation', new Address6('2001:db8::1').getType(), 'Documentation');
    check('type-nat64-well-known', new Address6('64:ff9b::c000:221').getType(), 'NAT64 (well-known)');
    check('type-nat64-local-use', new Address6('64:ff9b:1::1').getType(), 'NAT64 (local-use)');
    check('type-link-local', new Address6('fe80::1').getType(), 'Link-local unicast');
    check('type-global', new Address6('2606:4700::1111').getType(), 'Global unicast');
    check('type-loopback', new Address6('::1').getType(), 'Loopback');
    check('type-unspecified', new Address6('::').getType(), 'Unspecified');
  });

  // The RFC 6052 encoding vectors and the documented defaults.
  add('F-nat64-rfc6052-vectors', () => {
    check('encode-32', Address6.fromAddress4Nat64('192.0.2.33', '2001:db8::/32').correctForm(), '2001:db8:c000:221::');
    check('encode-40', Address6.fromAddress4Nat64('192.0.2.33', '2001:db8:100::/40').correctForm(), '2001:db8:1c0:2:21::');
    check('encode-48', Address6.fromAddress4Nat64('192.0.2.33', '2001:db8:122::/48').correctForm(), '2001:db8:122:c000:2:2100::');
    check('encode-56', Address6.fromAddress4Nat64('192.0.2.33', '2001:db8:122:300::/56').correctForm(), '2001:db8:122:3c0:0:221::');
    check('encode-64', Address6.fromAddress4Nat64('192.0.2.33', '2001:db8:122:344::/64').correctForm(), '2001:db8:122:344:c0:2:2100:0');
    check('encode-96', Address6.fromAddress4Nat64('192.0.2.33', '2001:db8:122:344::/96').correctForm(), '2001:db8:122:344::c000:221');
    check('default-encode', Address6.fromAddress4Nat64('192.0.2.33').correctForm(), '64:ff9b::c000:221');
    check('default-decode', new Address6('64:ff9b::c000:221').toAddress4Nat64().correctForm(), '192.0.2.33');
    check('decode-48', new Address6('2001:db8:122:c000:2:2100::').toAddress4Nat64('2001:db8:122::/48').correctForm(), '192.0.2.33');
    check('decode-outside', new Address6('2001:db8::1').toAddress4Nat64(), null);
  });

  // Values already classified correctly keep their answers.
  add('F-existing-classifications', () => {
    check('link-local-fe80-64', new Address6('fe80::baf6:b1ff:fe15:4885').isLinkLocal(), true);
    check('link-local-non-link-local', new Address6('2001:db8::1').isLinkLocal(), false);
    check('ula-in', new Address6('fc00::1').isULA(), true);
    check('ula-out-high', new Address6('fbff:ffff:ffff:ffff:ffff:ffff:ffff:ffff').isULA(), false);
    check('ula-out-link-local', new Address6('fe80::1').isULA(), false);
    check('mapped4-dotted', new Address6('::ffff:127.0.0.1').isMapped4(), true);
    check('mapped4-hex', new Address6('::ffff:7f00:1').isMapped4(), true);
    check('mapped4-nat64', new Address6('64:ff9b::192.0.2.1').isMapped4(), false);
    check('mapped4-compatible', new Address6('::1.2.3.4').isMapped4(), false);
    check('loopback-native', new Address6('::1').isLoopback(), true);
    check('multicast-native', new Address6('ff02::1').isMulticast(), true);
    check('unspecified-native', new Address6('::').isUnspecified(), true);
  });

  // The IPv4 special-range checks keep their answers.
  add('F-ipv4-existing-classifications', () => {
    check('v4-private', new Address4('10.0.0.1').isPrivate(), true);
    check('v4-public', new Address4('8.8.8.8').isPrivate(), false);
    check('v4-public-loopback', new Address4('8.8.8.8').isLoopback(), false);
    check('v4-loopback', new Address4('127.0.0.1').isLoopback(), true);
    check('v4-link-local', new Address4('169.254.1.1').isLinkLocal(), true);
    check('v4-multicast', new Address4('224.0.0.1').isMulticast(), true);
    check('v4-broadcast', new Address4('255.255.255.255').isBroadcast(), true);
    check('v4-cgnat', new Address4('100.64.0.1').isCGNAT(), true);
    check('v4-unspecified', new Address4('0.0.0.0').isUnspecified(), true);
  });

  // Prefix-bearing host strings are valid input and keep their address.
  add('F-prefix-bearing-input', () => {
    check('v4-valid-prefix-host', Address4.isValid('192.168.1.5/24'), true);
    check('v6-valid-prefix-host', Address6.isValid('2001:db8::1/64'), true);
    check('v4-correct-form', new Address4('192.168.1.5/24').correctForm(), '192.168.1.5');
    check('v6-correct-form', new Address6('2001:db8::1/64').correctForm(), '2001:db8::1');
    check('v6-network-form', new Address6('2001:db8::1/64').networkForm(), '2001:db8::/64');
  });

  // The documented v4-in-v6 address conversions.
  add('F-v4-in-v6-shapes', () => {
    check('mapped-to4', new Address6('::ffff:192.168.0.1').to4().correctForm(), '192.168.0.1');
    check('mapped-to4-mask-default', new Address6('::ffff:192.168.0.1').to4().subnetMask, 32);
    check('mapped-to4-mask-prefixed', new Address6('::ffff:192.168.0.1/64').to4().subnetMask, 32);
    check('mapped-to4in6', new Address6('::ffff:192.168.0.1').to4in6(), '::ffff:192.168.0.1');
  });

  return cases;
};
