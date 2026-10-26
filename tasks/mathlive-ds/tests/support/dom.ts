/**
 * Test-side helpers for the hidden suites.
 *
 * DOM-level checks parse product output with a real HTML engine (jsdom) so that the
 * assertion is about what a browser would build, not about one spelling of an
 * escape. Nothing here imports product code: the harness must not depend on the
 * behaviour it is checking.
 */

const JSDOM_MODULE =
  process.env.JSDOM_PATH || '/opt/hidden-deps/node_modules/jsdom';

export const LIVE_SELECTOR =
  'img,script,svg,iframe,object,embed,[onerror],[onload]';

export function freshDom(
  html = '<!doctype html><html><body><div id="r"></div></body></html>'
): any {
  const { JSDOM } = require(JSDOM_MODULE);
  return new JSDOM(html, { url: 'https://example.test/' });
}

/** Parse an HTML or MathML fragment the way a page would, and return its container. */
export function parseFragment(markup: string): any {
  const dom = freshDom();
  const container = dom.window.document.getElementById('r');
  container.innerHTML = markup;
  return container;
}

export function liveCount(root: any): number {
  return root.querySelectorAll(LIVE_SELECTOR).length;
}

/** Text visible after the page has parsed the fragment. */
export function visibleText(markup: string): string {
  return parseFragment(markup).textContent;
}

/**
 * A browser-like environment for the DOM-level product entry points.
 *
 * The module is required once per test file, after the globals exist, because the
 * product registers custom elements and reads the current context while loading.
 */
let browserCache: any;

export function browserEnv(): any {
  if (browserCache) return browserCache;
  const dom = freshDom();
  const w: any = dom.window;
  for (const key of [
    'window',
    'document',
    'Node',
    'Element',
    'HTMLElement',
    'Text',
    'CustomEvent',
    'Event',
    'DocumentFragment',
    'ShadowRoot',
    'MutationObserver',
    'requestAnimationFrame',
    'cancelAnimationFrame',
    'getComputedStyle',
    'matchMedia',
    'CSSStyleSheet',
  ]) {
    if (key in w) (globalThis as any)[key] = w[key];
  }
  (globalThis as any).window = w;
  (globalThis as any).document = w.document;
  // The static renderer tries to load web fonts; keep that offline and quiet.
  w.document.fonts = { add() {}, [Symbol.iterator]: function* () {} };
  Object.defineProperty(w.document, 'readyState', { get: () => 'complete' });

  const product = require('../../src/mathlive');
  (globalThis as any).MathfieldElement.fontsDirectory = null;
  browserCache = { dom, window: w, product };
  return browserCache;
}

/** A DOM parser for strict XML checks of a serialized document. */
export function xmlDoc(xml: string): any {
  const dom = freshDom();
  return new dom.window.DOMParser().parseFromString(xml, 'application/xml');
}

export function xmlIsWellFormed(xml: string): boolean {
  const doc = xmlDoc(xml);
  return !doc.querySelector('parsererror') && doc.documentElement?.tagName !== 'parsererror';
}
