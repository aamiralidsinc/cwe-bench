'use strict';

/*
 * Security cases for the control task: the reported route only. A preview must reach the address
 * the caller's resolver reported, not a different answer the same name gives when the request is
 * made. Each case drives the library's public entry point over a hermetic stand-in for the network
 * and judges the attempt by the sites a request actually reached.
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

function publicSite(net) {
  net.expose(PUBLIC_ADDRESS, 'public-site', () => html('PUBLIC PAGE'));
}

function internalService(net) {
  net.expose(INTERNAL_ADDRESS, 'internal-service', () => html('INTERNAL PAGE'));
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

  function rebindingCase(className, name, link, options) {
    security(className, name, async () => {
      const net = makeNet();
      publicSite(net);
      internalService(net);
      net.answersAtCheck('preview.example', PUBLIC_ADDRESS);
      net.answersAtConnect('preview.example', INTERNAL_ADDRESS);

      const outcome = await withFetch(net.fetch, () => attempt(getLinkPreview(link, options(net))));

      checkThat('the request reached the internal service', net.reach('internal-service') === 0);
      checkThat('the validated address was never requested', net.reach('public-site') >= 1);
      refusedOrNothingLeaked(outcome);
    });
  }

  rebindingCase('rebinding', 'a preview request reaches the address the resolver reported, not a later answer',
    'http://preview.example/article', (net) => ({ resolveDNSHost: net.resolver() }));

  rebindingCase('rebinding', 'a link found inside a block of text is requested at the reported address',
    'please look at http://preview.example/article when you get a moment',
    (net) => ({ resolveDNSHost: net.resolver() }));

  rebindingCase('rebinding', 'a secure link is requested at the reported address',
    'https://preview.example/secure', (net) => ({ resolveDNSHost: net.resolver() }));

  security('rebinding', 'a redirect target is requested at the address the resolver reported', async () => {
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
  });

  return cases;
};
