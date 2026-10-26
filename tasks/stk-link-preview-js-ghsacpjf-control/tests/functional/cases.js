'use strict';

/*
 * Functional cases: the preview must keep working for every legitimate caller, next to the
 * hidden routes. Each case drives the library's public entry point against a hermetic network
 * and checks the returned preview, its reported url and the options that callers rely on.
 */

const { makeNet, page, withFetch, check, checkThat } = require('../support/net');

const PUBLIC_ADDRESS = '93.184.216.34';
const OTHER_PUBLIC_ADDRESS = '198.20.30.40';
const PUBLIC_IPV6_ADDRESS = '2606:4700:4700::8888';

function html(title) {
  return { status: 200, headers: { 'content-type': 'text/html' }, body: page(title) };
}

function redirectTo(location) {
  return { status: 302, headers: { location } };
}

module.exports = function ({ getLinkPreview, getPreviewFromContent }) {
  const cases = [];

  function functional(className, name, run) {
    cases.push({ classname: 'functional/' + className, name, run });
  }

  functional('public-preview', 'a public link previews with a resolver supplied', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => html('PUBLIC PAGE'));
    net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);

    const result = await withFetch(net.fetch, () =>
      getLinkPreview('http://preview.example/article', { resolveDNSHost: net.resolver() }),
    );

    check('title', result.title, 'PUBLIC PAGE');
    check('description', result.description, 'PUBLIC PAGE description');
    check('mediaType', result.mediaType, 'website');
    check('contentType', result.contentType, 'text/html');
  });

  functional('public-preview', 'a public IPv6 answer is accepted', async () => {
    const net = makeNet();
    net.expose(PUBLIC_IPV6_ADDRESS, 'public-site', () => html('PUBLIC V6 PAGE'));
    net.answersAtCheck('v6.example', PUBLIC_IPV6_ADDRESS);
    net.answersAtConnect('v6.example', PUBLIC_IPV6_ADDRESS);

    const result = await withFetch(net.fetch, () =>
      getLinkPreview('http://v6.example/', { resolveDNSHost: net.resolver() }),
    );

    check('title', result.title, 'PUBLIC V6 PAGE');
  });

  functional('public-preview', 'a public link previews without any resolver', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => html('PLAIN PAGE'));
    net.answersAtConnect('plain.example', PUBLIC_ADDRESS);

    const result = await withFetch(net.fetch, () => getLinkPreview('http://plain.example/hello'));

    check('title', result.title, 'PLAIN PAGE');
    check('url', result.url, 'http://plain.example/hello');
  });

  functional('public-preview', 'a public link given as an address literal previews', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => html('LITERAL PAGE'));

    const result = await withFetch(net.fetch, () => getLinkPreview(`http://${PUBLIC_ADDRESS}:8080/page`));

    check('title', result.title, 'LITERAL PAGE');
    check('url', result.url, `http://${PUBLIC_ADDRESS}:8080/page`);
  });

  functional('redirects', 'the follow mode follows a chain of public redirects', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('http://middle.example/step'));
    net.expose(OTHER_PUBLIC_ADDRESS, 'middle-site', (url) =>
      new URL(url).pathname === '/step' ? redirectTo('/final') : html('FINAL PAGE'),
    );
    net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);
    net.answersAtCheck('middle.example', OTHER_PUBLIC_ADDRESS);
    net.answersAtConnect('middle.example', OTHER_PUBLIC_ADDRESS);

    const result = await withFetch(net.fetch, () =>
      getLinkPreview('http://preview.example/', { followRedirects: 'follow', resolveDNSHost: net.resolver() }),
    );

    check('title', result.title, 'FINAL PAGE');
    checkThat('the followed chain did not reach the second public page', net.reach('middle-site') >= 1);
  });

  functional('redirects', 'the manual mode still asks the caller about a redirect', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', (url) =>
      new URL(url).pathname === '/' ? redirectTo('http://preview.example/next') : html('NEXT PAGE'),
    );
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);

    let asked = null;
    const result = await withFetch(net.fetch, () =>
      getLinkPreview('http://preview.example/', {
        followRedirects: 'manual',
        handleRedirects: (baseURL, forwardedURL) => {
          asked = { baseURL, forwardedURL };
          const base = new URL(baseURL);
          const forwarded = new URL(forwardedURL);
          return forwarded.hostname === base.hostname;
        },
      }),
    );

    check('title', result.title, 'NEXT PAGE');
    checkThat('handleRedirects was not consulted', asked !== null);
    check('handleRedirects base hostname', new URL(asked.baseURL).hostname, 'preview.example');
    check('handleRedirects forwarded hostname', new URL(asked.forwardedURL).hostname, 'preview.example');
  });

  functional('redirects', 'the error mode still refuses a redirect', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('http://preview.example/next'));
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);

    let refused = false;
    await withFetch(net.fetch, () =>
      getLinkPreview('http://preview.example/', { followRedirects: 'error' }).catch(() => {
        refused = true;
      }),
    );

    checkThat('the redirect was followed', refused);
  });

  functional('redirects', 'the manual mode without an approval function is refused', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => html('PUBLIC PAGE'));
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);

    let message = '';
    await withFetch(net.fetch, () =>
      getLinkPreview('http://preview.example/', { followRedirects: 'manual' }).catch((e) => {
        message = String(e && e.message);
      }),
    );

    check('refusal message', message, 'link-preview-js followRedirects is set to manual, but no handleRedirects function was provided');
    checkThat('the request was made anyway', net.reach('public-site') === 0);
  });

  functional('prefetched', 'a prefetched response is still parsed', async () => {
    const body =
      '<html><head><meta property="og:title" content="FROM CONTENT">' +
      '<meta property="og:description" content="parsed without fetching"></head><body></body></html>';

    const result = await getPreviewFromContent({
      url: 'https://content.example/page',
      headers: { 'content-type': 'text/html' },
      data: body,
    });

    check('title', result.title, 'FROM CONTENT');
    check('description', result.description, 'parsed without fetching');
    check('url', result.url, 'https://content.example/page');
  });

  return cases;
};
