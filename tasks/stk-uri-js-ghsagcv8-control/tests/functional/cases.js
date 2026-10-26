'use strict';

/*
 * Functional cases: legitimate URLs and the coupled values next to the hidden ones. Every
 * expectation below is what the pinned library already produces today (checked when the task was
 * built); these must keep working whatever the fix does.
 */

const BS = '\\';

function partsCase(URI, id, input, expected) {
  return {
    classname: 'functional/' + id,
    name: `${id}: ${JSON.stringify(input)} keeps its parsed parts`,
    run() {
      const p = URI.parse(input);
      for (const key of Object.keys(expected)) {
        const want = expected[key];
        const got = p[key];
        if (typeof want === 'function') {
          if (!want(got)) throw new Error(`parse(${JSON.stringify(input)}).${key} is ${JSON.stringify(got)}, expected ${want.description}`);
        } else if (got !== want) {
          throw new Error(`parse(${JSON.stringify(input)}).${key} is ${JSON.stringify(got)}, expected ${JSON.stringify(want)}`);
        }
      }
    },
  };
}

function accessorCase(URI, id, input, expected) {
  return {
    classname: 'functional/' + id,
    name: `${id}: ${JSON.stringify(input)} keeps its accessor values`,
    run() {
      const u = new URI(input);
      for (const key of Object.keys(expected)) {
        const want = expected[key];
        const got = u[key]();
        if (got !== want) {
          throw new Error(`new URI(${JSON.stringify(input)}).${key}() is ${JSON.stringify(got)}, expected ${JSON.stringify(want)}`);
        }
      }
    },
  };
}

const absent = (got) => !got;
absent.description = 'no host';

module.exports = function (URI) {
  const cases = [];
  const parts = (id, input, expected) => cases.push(partsCase(URI, id, input, expected));
  const acc = (id, input, expected) => cases.push(accessorCase(URI, id, input, expected));

  // Ordinary, already-correct URLs keep every part.
  parts('F-http-basic', 'http://evil.example/account', {
    protocol: 'http', hostname: 'evil.example', port: null, path: '/account',
    query: undefined, fragment: undefined, username: null, password: null, urn: undefined,
  });
  parts('F-https-userinfo', 'https://user:pass@example.org:8443/p?q=1#f', {
    protocol: 'https', hostname: 'example.org', port: '8443', path: '/p',
    query: 'q=1', fragment: 'f', username: 'user', password: 'pass', urn: undefined,
  });
  acc('F-https-userinfo-accessors', 'https://user:pass@example.org:8443/p?q=1#f', {
    protocol: 'https', hostname: 'example.org', port: '8443', path: '/p',
    query: 'q=1', fragment: 'f', username: 'user', password: 'pass',
  });

  // Delimiter forms that already resolve to a host today.
  parts('F-two-backslashes', 'http:' + BS.repeat(2) + 'evil.example/account', {
    protocol: 'http', hostname: 'evil.example', path: '/account',
  });
  parts('F-slash-backslash', 'http:/' + BS + 'evil.example/account', {
    protocol: 'http', hostname: 'evil.example', path: '/account',
  });
  parts('F-scheme-relative', '//evil.example/account', {
    protocol: null, hostname: 'evil.example', path: '/account',
  });

  // The scheme is stored as written.
  acc('F-protocol-case', 'HTTP://evil.example/account', {
    protocol: 'HTTP', hostname: 'evil.example', path: '/account',
  });

  // Strings without an authority keep their shape and are never given a host.
  parts('F-food-urn', 'food:///test/file.csv', {
    protocol: 'food', hostname: absent, path: '/test/file.csv', urn: undefined,
  });
  parts('F-file-url', 'file:///foo/bar/baz.html', {
    protocol: 'file', hostname: absent, path: '/foo/bar/baz.html', urn: undefined,
  });
  parts('F-userinfo-as-urn', 'user:pass@www.example.org:123/account', {
    protocol: 'user', hostname: absent, path: 'pass@www.example.org:123/account', urn: true,
  });
  parts('F-mailto', 'mailto:foo@example.org', {
    protocol: 'mailto', hostname: absent, path: 'foo@example.org', urn: true,
  });
  parts('F-javascript', 'javascript:alert(1)', {
    protocol: 'javascript', hostname: absent, path: 'alert(1)', urn: true,
  });
  parts('F-custom-scheme', 'custom:thing', {
    protocol: 'custom', hostname: absent, path: 'thing', urn: true,
  });
  parts('F-data-uri', 'data:text/plain,hello', {
    protocol: 'data', hostname: absent, path: 'text/plain,hello', urn: true,
  });
  parts('F-tel', 'tel:+123456', {
    protocol: 'tel', hostname: absent, path: '+123456', urn: true,
  });

  // An empty scheme still parses its authority.
  parts('F-empty-scheme-authority', '://user:pass@example.org:123/account', {
    protocol: null, hostname: 'example.org', username: 'user', password: 'pass',
    port: '123', path: '/account',
  });

  // Plain paths, including one with a literal space, keep their shape.
  parts('F-plain-path', '/foo/bar', {
    protocol: undefined, hostname: absent, path: '/foo/bar', urn: undefined,
  });
  parts('F-path-with-space', '/foo bar/baz', {
    protocol: undefined, hostname: absent, path: '/foo bar/baz',
  });
  parts('F-path-with-space-in-url', 'http://example.org/a b/c', {
    protocol: 'http', hostname: 'example.org', path: '/a b/c',
  });

  // Round trips do not change.
  {
    const input = 'http://example.org/a/b?c=d#e';
    cases.push({
      classname: 'functional/F-round-trip',
      name: 'F-round-trip: a correct URL string is unchanged',
      run() {
        const out = new URI(input).toString();
        if (out !== input) throw new Error(`round trip is ${JSON.stringify(out)}, expected ${JSON.stringify(input)}`);
      },
    });
  }

  return cases;
};
