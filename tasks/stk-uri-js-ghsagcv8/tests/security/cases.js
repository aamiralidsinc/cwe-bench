'use strict';

/*
 * Security cases: a URL a browser resolves to a host must be reported with that host by the
 * library, through both public entry points (the static parser and the URI constructor).
 * Expectations are browser-resolved hosts, written out here; nothing is computed with the
 * product.
 */

const BS = '\\';

function hostCase(URI, id, input, expected) {
  return {
    classname: 'security/' + id,
    name: `${id}: ${JSON.stringify(input)} reports host ${expected}`,
    run() {
      const direct = URI.parse(input);
      const gotDirect = direct.hostname;
      if (gotDirect !== expected) {
        throw new Error(`parse(${JSON.stringify(input)}).hostname is ${JSON.stringify(gotDirect)}, expected ${JSON.stringify(expected)}`);
      }
      const viaConstructor = new URI(input).hostname();
      if (viaConstructor !== expected) {
        throw new Error(`new URI(${JSON.stringify(input)}).hostname() is ${JSON.stringify(viaConstructor)}, expected ${JSON.stringify(expected)}`);
      }
    },
  };
}

function schemeRelativeCase(URI, id, input, expected) {
  return {
    classname: 'security/' + id,
    name: `${id}: scheme-relative ${JSON.stringify(input)} reports host ${expected}`,
    run() {
      const parts = URI.parse(input);
      if (parts.hostname !== expected) {
        throw new Error(`parse(${JSON.stringify(input)}).hostname is ${JSON.stringify(parts.hostname)}, expected ${JSON.stringify(expected)}`);
      }
      if (parts.protocol !== null) {
        throw new Error(`parse(${JSON.stringify(input)}).protocol is ${JSON.stringify(parts.protocol)}, expected a scheme-relative reference (null)`);
      }
      const viaConstructor = new URI(input).hostname();
      if (viaConstructor !== expected) {
        throw new Error(`new URI(${JSON.stringify(input)}).hostname() is ${JSON.stringify(viaConstructor)}, expected ${JSON.stringify(expected)}`);
      }
    },
  };
}

module.exports = function (URI) {
  const cases = [];
  const host = (id, input, expected) => cases.push(hostCase(URI, id, input, expected));
  const rel = (id, input, expected) => cases.push(schemeRelativeCase(URI, id, input, expected));

  // T1 - the authority marker after a web scheme is written with a run of slashes/backslashes.
  host('T1-http-none', 'http:evil.example/account', 'evil.example');
  host('T1-http-one-slash', 'http:/evil.example/account', 'evil.example');
  host('T1-http-three-slashes', 'http:' + '/'.repeat(3) + 'evil.example/account', 'evil.example');
  host('T1-http-five-slashes', 'http:' + '/'.repeat(5) + 'evil.example/account', 'evil.example');
  host('T1-http-one-backslash', 'http:' + BS + 'evil.example/account', 'evil.example');
  host('T1-http-three-backslashes', 'http:' + BS.repeat(3) + 'evil.example/account', 'evil.example');
  host('T1-http-four-backslashes', 'http:' + BS.repeat(4) + 'evil.example/account', 'evil.example');
  host('T1-http-mixed-run', 'http:/' + BS + '/evil.example/account', 'evil.example');
  host('T1-https-none', 'https:evil.example/account', 'evil.example');
  host('T1-ftp-one-slash', 'ftp:/evil.example/pub', 'evil.example');
  host('T1-ws-three-slashes', 'ws:' + '/'.repeat(3) + 'evil.example/socket', 'evil.example');
  host('T1-wss-backslashes', 'wss:' + BS.repeat(3) + 'evil.example/socket', 'evil.example');

  // T2 - the same delimiter written with an upper-case or mixed-case scheme.
  host('T2-http-upper-none', 'HTTP:evil.example/account', 'evil.example');
  host('T2-https-upper-slashes', 'HTTPS:///evil.example/account', 'evil.example');
  host('T2-http-mixed-backslash', 'HtTp:' + BS + 'evil.example/account', 'evil.example');
  host('T2-ftp-upper', 'FTP:evil.example/pub', 'evil.example');
  host('T2-wss-mixed', 'WsS:' + BS.repeat(3) + 'evil.example/socket', 'evil.example');

  // T3 - scheme-relative references: the authority marker at the start of the string.
  rel('T3-two-backslashes', BS.repeat(2) + 'evil.example/account', 'evil.example');
  rel('T3-three-backslashes', BS.repeat(3) + 'evil.example/account', 'evil.example');
  rel('T3-slash-backslash', '/' + BS + 'evil.example/account', 'evil.example');
  rel('T3-backslash-slash', BS + '/evil.example/account', 'evil.example');
  rel('T3-three-slashes', '/'.repeat(3) + 'evil.example/account', 'evil.example');
  rel('T3-four-slashes', '/'.repeat(4) + 'evil.example/account', 'evil.example');

  // T5 - characters a browser drops before it starts parsing.
  host('T5-leading-spaces', '  http://evil.example/account', 'evil.example');
  host('T5-leading-tabs', '\t\thttp://evil.example/account', 'evil.example');
  host('T5-leading-newline', '\nhttp://evil.example/account', 'evil.example');
  host('T5-leading-nul', '\u0000http://evil.example/account', 'evil.example');
  host('T5-embedded-tab', 'ht\ttp://evil.example/account', 'evil.example');
  host('T5-embedded-newline', 'http:\n//evil.example/account', 'evil.example');
  host('T5-leading-space-no-slashes', '  http:evil.example/account', 'evil.example');

  return cases;
};
