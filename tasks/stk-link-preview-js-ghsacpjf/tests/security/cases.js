'use strict';

/*
 * Security cases: every request the library makes must reach the public address the caller's
 * resolver reported, and nothing else. Each case drives the library's public entry point with a
 * hermetic network, and judges the attempt by the sites a request actually reached.
 */

const { makeNet, page, withFetch, checkThat } = require('../support/net');

const PUBLIC_ADDRESS = '93.184.216.34';
const OTHER_PUBLIC_ADDRESS = '198.20.30.40';
const INTERNAL_ADDRESS = '127.0.0.2';

function html(title) {
  return { status: 200, headers: { 'content-type': 'text/html' }, body: page(title) };
}

function redirectTo(location) {
  return { status: 302, headers: { location } };
}

function publicSite(net, address) {
  net.expose(address || PUBLIC_ADDRESS, 'public-site', () => html('PUBLIC PAGE'));
}

function internalService(net, address) {
  net.expose(address || INTERNAL_ADDRESS, 'internal-service', () => html('INTERNAL PAGE'));
}

/** Runs the call and reports whether it refused, without hiding the value when it did not. */
async function attempt(promise) {
  try {
    return { refused: false, value: await promise };
  } catch (e) {
    return { refused: true, error: e };
  }
}

function refusedOrNothingLeaked(outcome) {
  if (!outcome.refused) {
    checkThat(
      `the preview returned the internal service's page (${JSON.stringify(outcome.value && outcome.value.title)})`,
      !outcome.value || outcome.value.title !== 'INTERNAL PAGE',
    );
  }
}

module.exports = function ({ getLinkPreview }) {
  const cases = [];

  function security(className, name, run) {
    cases.push({ classname: 'security/' + className, name, run });
  }

  // -- a name whose answer changes between the check and the request ---------------------

  security(
    'rebinding',
    'a preview request reaches the address the resolver reported, not a later answer',
    async () => {
      const net = makeNet();
      publicSite(net);
      internalService(net);
      net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
      net.answersAtConnect('preview.example', INTERNAL_ADDRESS);

      const outcome = await withFetch(net.fetch, () =>
        attempt(getLinkPreview('http://preview.example/article', { resolveDNSHost: net.resolver() })),
      );

      checkThat('the request reached the internal service', net.reach('internal-service') === 0);
      checkThat('the validated address was never requested', net.reach('public-site') >= 1);
      refusedOrNothingLeaked(outcome);
    },
  );

  security(
    'rebinding',
    'a redirect target is requested at the address the resolver reported',
    async () => {
      const net = makeNet();
      net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('http://hop.example/next'));
      net.expose(OTHER_PUBLIC_ADDRESS, 'hop-site', () => html('HOP PAGE'));
      internalService(net);
      net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
      net.answersAtConnect('preview.example', PUBLIC_ADDRESS);
      net.answersAtCheck('hop.example', OTHER_PUBLIC_ADDRESS);
      net.answersAtConnect('hop.example', INTERNAL_ADDRESS);

      const outcome = await withFetch(net.fetch, () =>
        attempt(
          getLinkPreview('http://preview.example/', {
            followRedirects: 'manual',
            handleRedirects: () => true,
            resolveDNSHost: net.resolver(),
          }),
        ),
      );

      checkThat('the redirect target reached the internal service', net.reach('internal-service') === 0);
      checkThat('the redirect target was not requested at the reported address', net.reach('hop-site') >= 1);
      refusedOrNothingLeaked(outcome);
    },
  );

  // -- answers that are not a public address ---------------------------------------------

  const nonPublicAnswers = [
    ['ipv6-loopback', '::1'],
    ['ipv6-mapped-loopback', '::ffff:127.0.0.1'],
    ['ipv6-mapped-loopback-hex', '::ffff:7f00:1'],
    ['ipv6-mapped-link-local', '::ffff:a9fe:a9fe'],
    ['ipv6-link-local', 'fe80::1'],
    ['ipv6-link-local-zoned', 'fe80::1%eth0'],
    ['ipv6-unique-local', 'fc00::1'],
    ['ipv6-nat64-link-local', '64:ff9b::a9fe:a9fe'],
    ['ipv4-unspecified', '0.0.0.0'],
  ];

  for (const [id, answer] of nonPublicAnswers) {
    security('address-answer', `a resolver answer of ${answer} refuses the request`, async () => {
      const net = makeNet();
      internalService(net, answer);
      net.answersAtCheck('v6.example', answer);
      net.answersAtConnect('v6.example', answer);

      const outcome = await withFetch(net.fetch, () =>
        attempt(getLinkPreview('http://v6.example/', { resolveDNSHost: net.resolver() })),
      );

      checkThat('the request reached the internal service', net.reach('internal-service') === 0);
      checkThat('the request was not refused', outcome.refused);
    });
  }

  security('address-answer', 'a resolver answer that is not an address refuses the request', async () => {
    const net = makeNet();
    internalService(net);
    net.answersAtCheck('odd.example', 'not-an-address');
    net.answersAtConnect('odd.example', INTERNAL_ADDRESS);

    const outcome = await withFetch(net.fetch, () =>
      attempt(getLinkPreview('http://odd.example/', { resolveDNSHost: net.resolver() })),
    );

    checkThat('the request reached the internal service', net.reach('internal-service') === 0);
    checkThat('the request was not refused', outcome.refused);
  });

  // -- links whose own host is not a public address --------------------------------------

  const nonPublicLiterals = ['100.64.0.1', '192.0.2.5', '198.51.100.7', '203.0.113.9'];

  for (const literal of nonPublicLiterals) {
    security('address-link', `a link to ${literal} is refused before any request`, async () => {
      const net = makeNet();
      internalService(net, literal);

      const outcome = await withFetch(net.fetch, () =>
        attempt(getLinkPreview(`http://${literal}:8080/status`)),
      );

      checkThat('the request reached the internal service', net.reach('internal-service') === 0);
      checkThat('the request was not refused', outcome.refused);
    });
  }

  // -- the hops of a followed redirect chain ---------------------------------------------

  security('redirects', 'a followed redirect does not reach an address the resolver refuses', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('http://hidden.example/secret'));
    internalService(net);
    net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);
    net.answersAtCheck('hidden.example', INTERNAL_ADDRESS);
    net.answersAtConnect('hidden.example', INTERNAL_ADDRESS);

    const outcome = await withFetch(net.fetch, () =>
      attempt(getLinkPreview('http://preview.example/', { followRedirects: 'follow', resolveDNSHost: net.resolver() })),
    );

    checkThat('the redirect reached the internal service', net.reach('internal-service') === 0);
    checkThat('the public page was never requested', net.reach('public-site') >= 1);
    refusedOrNothingLeaked(outcome);
  });

  security('redirects', 'a followed redirect to a private address literal is not requested', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('http://169.254.169.254/latest/meta-data/'));
    net.expose('169.254.169.254', 'internal-service', () => html('INTERNAL PAGE'));
    net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);

    const outcome = await withFetch(net.fetch, () =>
      attempt(getLinkPreview('http://preview.example/', { followRedirects: 'follow', resolveDNSHost: net.resolver() })),
    );

    checkThat('the redirect reached the internal service', net.reach('internal-service') === 0);
    checkThat('the public page was never requested', net.reach('public-site') >= 1);
    refusedOrNothingLeaked(outcome);
  });

  security('redirects', 'a protocol-relative redirect target is resolved before it is requested', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('//169.254.169.254/latest/meta-data/'));
    net.expose('169.254.169.254', 'internal-service', () => html('INTERNAL PAGE'));
    net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);

    const outcome = await withFetch(net.fetch, () =>
      attempt(getLinkPreview('http://preview.example/', { followRedirects: 'follow', resolveDNSHost: net.resolver() })),
    );

    checkThat('the redirect reached the internal service', net.reach('internal-service') === 0);
    checkThat('the public page was never requested', net.reach('public-site') >= 1);
    refusedOrNothingLeaked(outcome);
  });

  security('redirects', 'every hop of a redirect chain is checked, not only the first', async () => {
    const net = makeNet();
    net.expose(PUBLIC_ADDRESS, 'public-site', () => redirectTo('http://middle.example/step'));
    net.expose(OTHER_PUBLIC_ADDRESS, 'middle-site', () => redirectTo('http://hidden.example/secret'));
    internalService(net);
    net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
    net.answersAtConnect('preview.example', PUBLIC_ADDRESS);
    net.answersAtCheck('middle.example', OTHER_PUBLIC_ADDRESS);
    net.answersAtConnect('middle.example', OTHER_PUBLIC_ADDRESS);
    net.answersAtCheck('hidden.example', INTERNAL_ADDRESS);
    net.answersAtConnect('hidden.example', INTERNAL_ADDRESS);

    const outcome = await withFetch(net.fetch, () =>
      attempt(getLinkPreview('http://preview.example/', { followRedirects: 'follow', resolveDNSHost: net.resolver() })),
    );

    checkThat('the chain reached the internal service', net.reach('internal-service') === 0);
    checkThat('the first public page was never requested', net.reach('public-site') >= 1);
    checkThat('the second public page was never requested', net.reach('middle-site') >= 1);
    refusedOrNothingLeaked(outcome);
  });

  return cases;
};
