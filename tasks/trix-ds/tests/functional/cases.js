'use strict';

/*
 * Functional cases: legitimate documents keep rendering exactly as before. These are written so
 * they pass both on the unfixed tree and on any correct fix, including the preservation clauses of
 * the report (links keep their destination and text, other formatting and attachment captions are
 * untouched).
 */

const {
  textDocument,
  stringBlock,
  attachmentBlock,
  fileAttachment,
  renderJSON,
} = require('../support/checks');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function anchors(element) {
  return Array.from(element.querySelectorAll('a[href]'));
}

module.exports = function ({ T }) {
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: `functional/documents/${id}`, name, run });

  for (const [ id, href ] of [
    [ 'https', 'https://example.test/articles/1' ],
    [ 'mailto', 'mailto:editor@example.test' ],
    [ 'relative', '/articles/1' ],
  ]) {
    add(`safe-link-${id}`, `a safe ${id} destination still renders with its text`, () => {
      const element = renderJSON(T, textDocument('Click me', { href }));
      const found = anchors(element);
      assert(found.length === 1, `expected one rendered link, found ${found.length}`);
      assert(found[0].getAttribute('href') === href, `destination changed to ${found[0].getAttribute('href')}`);
      assert(found[0].textContent === 'Click me', `link text changed to ${JSON.stringify(found[0].textContent)}`);
    });
  }

  add('round-trip', 'a safe destination survives a save and reload of the document', () => {
    const document = T.deserializeFromContentType(textDocument('Click me', { href: 'https://example.test/keep' }), 'application/json');
    const saved = T.serializeToContentType(document, 'application/json');
    const element = renderJSON(T, saved);
    const found = anchors(element);
    assert(found.length === 1, `expected one rendered link after reload, found ${found.length}`);
    assert(found[0].getAttribute('href') === 'https://example.test/keep', 'destination changed after reload');
    assert(found[0].textContent === 'Click me', 'link text changed after reload');
  });

  add('formatting', 'other formatting still renders next to a safe link', () => {
    const element = renderJSON(T, textDocument('Click me', { bold: true, italic: true, href: 'https://example.test/b' }));
    assert(anchors(element).length === 1, 'expected one rendered link');
    assert(element.querySelector('strong') !== null, 'bold formatting was lost');
    assert(element.querySelector('em') !== null, 'italic formatting was lost');
    assert(element.textContent.includes('Click me'), 'link text was lost');
  });

  add('block-attributes', 'block formatting still renders next to a safe link', () => {
    const json = JSON.stringify([ stringBlock('Quoted click me', { href: 'https://example.test/q' }, [ 'quote' ]) ]);
    const element = renderJSON(T, json);
    assert(element.querySelector('blockquote') !== null, 'block quote was lost');
    assert(anchors(element).length === 1, 'expected one rendered link');
    assert(element.textContent.includes('Quoted click me'), 'text was lost');
  });

  add('refused-link-keeps-text', 'a refused destination keeps the link text and other formatting', () => {
    const element = renderJSON(T, textDocument('Keep this text', { bold: true, href: 'javascript:alert(1)' }));
    assert(element.textContent.includes('Keep this text'), 'text was lost when the destination was refused');
    assert(element.querySelector('strong') !== null, 'bold formatting was lost when the destination was refused');
  });

  add('mention', 'a safe mention destination still renders with its text', () => {
    const element = renderJSON(T, textDocument('@alex', { mention: 'https://example.test/people/alex' }));
    const found = anchors(element);
    assert(found.length === 1, `expected one rendered mention link, found ${found.length}`);
    assert(found[0].getAttribute('href') === 'https://example.test/people/alex', 'mention destination changed');
    assert(element.textContent.includes('@alex'), 'mention text was lost');
  });

  add('mention-plain-text', 'text without a mention attribute still renders as plain text', () => {
    const element = renderJSON(T, textDocument('plain words', {}));
    assert(anchors(element).length === 0, 'plain text gained a link');
    assert(element.textContent.includes('plain words'), 'plain text was lost');
  });

  add('attachment-link', 'a safe attachment link still renders with its caption', () => {
    const element = renderJSON(
      T,
      attachmentBlock({ caption: 'my caption', link: 'https://example.test/docs/1' }, fileAttachment()),
    );
    const found = anchors(element);
    assert(found.length === 1, `expected one rendered attachment link, found ${found.length}`);
    assert(found[0].getAttribute('href') === 'https://example.test/docs/1', 'attachment destination changed');
    assert(element.textContent.includes('my caption'), 'attachment caption was lost');
    assert(element.querySelector('figure') !== null, 'attachment figure was lost');
  });

  add('attachment-own-href', 'an attachment download destination still renders', () => {
    const element = renderJSON(
      T,
      attachmentBlock({}, fileAttachment({ href: 'https://example.test/files/report.pdf' })),
    );
    const found = anchors(element);
    assert(found.length === 1, `expected one rendered download link, found ${found.length}`);
    assert(found[0].getAttribute('href') === 'https://example.test/files/report.pdf', 'download destination changed');
    assert(element.textContent.includes('report.pdf'), 'attachment name was lost');
  });

  add('attachment-refused-link-keeps-caption', 'a refused attachment destination keeps the caption', () => {
    const element = renderJSON(
      T,
      attachmentBlock({ caption: 'my caption', link: 'javascript:alert(1)' }, fileAttachment()),
    );
    assert(element.textContent.includes('my caption'), 'caption was lost when the destination was refused');
    assert(element.querySelector('figure') !== null, 'figure was lost when the destination was refused');
  });

  return cases;
};
