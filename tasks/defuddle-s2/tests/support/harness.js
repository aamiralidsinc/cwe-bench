'use strict';

/*
 * Shared document helpers for the hidden cases. Documents are parsed with linkedom, the DOM
 * implementation the project uses by default; the small polyfills mirror the project's own
 * linkedom helper so the product sees the same document shape in the suites as in its tests.
 */

const { parseHTML } = require('linkedom');

function makeDoc(html, url) {
  const { document } = parseHTML(html);
  if (!document.styleSheets) document.styleSheets = [];
  if (document.defaultView && !document.defaultView.getComputedStyle) {
    document.defaultView.getComputedStyle = () => ({ display: '' });
  }
  if (url) document.URL = url;
  return document;
}

function responseDoc(html) {
  return makeDoc(`<html><body>${html}</body></html>`);
}

const URI_ATTRS = ['href', 'src', 'action', 'formaction', 'xlink:href'];
const UNSAFE_TAGS = ['script', 'object', 'embed', 'applet', 'base'];
const SCHEMES = ['javascript:', 'data:text/html'];

function normalizeUrl(value) {
  return String(value).replace(/[\s\u0000-\u001F]+/g, '').toLowerCase();
}

function executableMarkup(html) {
  const doc = responseDoc(html);
  const found = [];
  for (const el of Array.from(doc.querySelectorAll('*'))) {
    const tag = String(el.tagName || '').toLowerCase();
    if (UNSAFE_TAGS.includes(tag)) found.push(`<${tag}> element`);
    for (const attr of Array.from(el.attributes || [])) {
      const name = String(attr.name || '').toLowerCase();
      if (name.startsWith('on')) found.push(`${name} attribute`);
      else if (name === 'srcdoc') found.push('srcdoc attribute');
      else if (URI_ATTRS.includes(name)) {
        const value = normalizeUrl(attr.value);
        if (SCHEMES.some(s => value.startsWith(s))) found.push(`${name}=${attr.value}`);
      }
    }
  }
  return found;
}

function assertNoExecutable(html) {
  const bad = executableMarkup(html);
  if (bad.length > 0) {
    throw new Error('returned content carries executable markup: ' + bad.join(', '));
  }
}

function attr(html, selector, name) {
  const doc = responseDoc(html);
  const el = doc.querySelector(selector);
  if (!el) throw new Error(`expected a ${selector} element in the returned content`);
  return el.getAttribute(name);
}

function hasElement(html, selector) {
  return !!responseDoc(html).querySelector(selector);
}

function text(html) {
  return responseDoc(html).textContent || '';
}

module.exports = { makeDoc, responseDoc, executableMarkup, assertNoExecutable, attr, hasElement, text };
