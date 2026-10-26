'use strict';

/*
 * A hermetic stand-in for the network. It replaces the global fetch with one that
 * routes every request through a table the case declares:
 *
 *   expose(address, name, handler)  a site reachable at an IP address
 *   answersAtCheck(host, address)   what the caller's resolver reports for a name
 *   answersAtConnect(host, address) what the network does with the name when the request is made
 *
 * The second table is what lets a case model a name whose answer changes after it has been
 * resolved. A case's side effect is the list of sites a request actually reached; no sockets
 * are opened and nothing leaves the process.
 */

const { isIP } = require('node:net');

function canon(address) {
  const bare = String(address).replace(/^\[/, '').replace(/\]$/, '').toLowerCase();

  if (isIP(bare) === 6) {
    // One address, one key: the URL parser normalises the double-colon forms it accepts.
    try {
      const parsed = new URL('http://stated.invalid/');
      parsed.hostname = `[${bare}]`;
      return parsed.hostname.replace(/^\[/, '').replace(/\]$/, '');
    } catch (e) {
      return bare;
    }
  }

  return bare;
}

function makeNet() {
  const sites = new Map(); // address -> { name, handler }
  const atCheck = new Map(); // host -> address the resolver reports
  const atConnect = new Map(); // host -> address the network uses
  const contacts = []; // every request that reached a site
  const calls = []; // every fetch() the product made

  function expose(address, name, handler) {
    sites.set(canon(address), { name, handler });
  }

  function answersAtCheck(host, address) {
    atCheck.set(canon(host), address);
  }

  function answersAtConnect(host, address) {
    atConnect.set(canon(host), address);
  }

  function addressAtConnect(host) {
    const key = canon(host);
    if (isIP(key)) {
      return key;
    }
    if (!atConnect.has(key)) {
      return null;
    }
    return atConnect.get(key);
  }

  function makeResponse(record, url) {
    const response = new Response(record.body === undefined ? '' : record.body, {
      status: record.status || 200,
      headers: record.headers || {},
    });
    Object.defineProperty(response, 'url', { value: url });
    return response;
  }

  async function fetchThrough(input, init) {
    init = init || {};
    const start = typeof input === 'string' ? input : String(input && input.url ? input.url : input);
    calls.push({ url: start, redirect: init.redirect });

    let current = start;
    let hops = 0;

    for (;;) {
      const parsed = new URL(current);

      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        throw new TypeError('fetch failed');
      }

      const address = addressAtConnect(parsed.hostname);

      if (!address) {
        throw new TypeError(`fetch failed: getaddrinfo ENOTFOUND ${parsed.hostname}`);
      }

      const site = sites.get(canon(address));
      contacts.push({ url: current, address: canon(address), site: site ? site.name : null });

      if (!site) {
        throw new TypeError('fetch failed');
      }

      const record = site.handler(current, parsed) || {};
      const location = record.headers && (record.headers.location || record.headers.Location);
      const isRedirect = record.status >= 300 && record.status < 400 && Boolean(location);

      if (isRedirect) {
        if (init.redirect === 'follow') {
          hops += 1;
          if (hops > 20) {
            throw new TypeError('fetch failed: redirect count exceeded');
          }
          current = new URL(location, current).href;
          continue;
        }
        if (init.redirect === 'error' || init.redirect === undefined) {
          throw new TypeError('fetch failed: unexpected redirect');
        }
      }

      return makeResponse(record, current);
    }
  }

  /** The resolver the case hands to the product: closed over the addresses it may report. */
  function resolver() {
    return async function resolveDNSHost(url) {
      const parsed = new URL(String(url));
      const host = canon(parsed.hostname);

      if (isIP(host)) {
        return host;
      }
      if (!atCheck.has(host)) {
        throw new Error(`resolver was asked for a host the case did not declare: ${host}`);
      }
      return atCheck.get(host);
    };
  }

  function reach(name) {
    return contacts.filter((contact) => contact.site === name).length;
  }

  return {
    fetch: fetchThrough,
    expose,
    answersAtCheck,
    answersAtConnect,
    resolver,
    reach,
    contacts,
    calls,
  };
}

/** A page whose OpenGraph tags let a case tell one site's content from another's. */
function page(title) {
  return (
    '<html><head>' +
    `<meta property="og:title" content="${title}">` +
    `<meta property="og:description" content="${title} description">` +
    `<meta property="og:type" content="website">` +
    '</head><body><p>body</p></body></html>'
  );
}

/** Runs fn with the stand-in fetch installed, and restores the real one afterwards. */
async function withFetch(fake, fn) {
  const previous = globalThis.fetch;
  globalThis.fetch = fake;
  try {
    return await fn();
  } finally {
    globalThis.fetch = previous;
  }
}

/** Expected value check; a mismatch fails the case with both values in the message. */
function check(label, actual, expected) {
  if (actual !== expected) {
    throw new Error(`${label} is ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
  }
}

function checkThat(label, condition) {
  if (!condition) {
    throw new Error(label);
  }
}

module.exports = { makeNet, page, withFetch, check, checkThat };
