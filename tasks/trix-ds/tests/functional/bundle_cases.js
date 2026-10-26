'use strict';

/*
 * Functional cases through the prebuilt asset shipped with the repository: legitimate documents
 * keep rendering exactly as before.
 */

const { textDocument, attachmentBlock, fileAttachment } = require('../support/checks');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

module.exports = function ({ Trix }) {
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: `functional/prebuilt-asset/${id}`, name, run });

  const render = (json) => Trix.views.DocumentView.render(Trix.Document.fromJSONString(json));

  add('safe-link', 'a safe destination still renders through the shipped asset', () => {
    const element = render(textDocument('Click me', { href: 'https://example.test/keep' }));
    const links = Array.from(element.querySelectorAll('a[href]'));
    assert(links.length === 1, `expected one rendered link, found ${links.length}`);
    assert(links[0].getAttribute('href') === 'https://example.test/keep', 'destination changed');
    assert(links[0].textContent === 'Click me', 'link text changed');
  });

  add('attachment', 'an attachment still renders its download link and caption through the shipped asset', () => {
    const element = render(
      attachmentBlock({ caption: 'my caption' }, fileAttachment({ href: 'https://example.test/files/report.pdf' })),
    );
    const links = Array.from(element.querySelectorAll('a[href]'));
    assert(links.length === 1, `expected one rendered download link, found ${links.length}`);
    assert(links[0].getAttribute('href') === 'https://example.test/files/report.pdf', 'download destination changed');
    assert(element.textContent.includes('my caption'), 'caption was lost');
  });

  return cases;
};
