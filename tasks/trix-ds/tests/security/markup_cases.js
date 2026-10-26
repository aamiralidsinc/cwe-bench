'use strict';

/*
 * Security cases reached through the editor's markup entry point: markup pasted or dropped into
 * the editor is parsed into a document and rendered. Every case asserts that no value carried by
 * the markup becomes an executable destination on a rendered link.
 */

const {
  fileAttachment,
  attachmentFigureHTML,
  expectNoExecutableDestination,
} = require('../support/checks');

module.exports = function ({ T }) {
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: `security/markup/${id}`, name, run });

  add('mention', 'a mention destination in pasted markup is not rendered', () => {
    const html = '<div><a data-trix-mention="javascript:alert(6)">@alex</a></div>';
    expectNoExecutableDestination(T.DocumentView.render(T.HTMLParser.parse(html).getDocument()), 'pasted mention');
  });

  add('mention-mixed-case', 'a mixed-case mention destination in pasted markup is not rendered', () => {
    const html = '<div><a data-trix-mention="JavaScript:alert(6)">@alex</a></div>';
    expectNoExecutableDestination(T.DocumentView.render(T.HTMLParser.parse(html).getDocument()), 'mixed-case pasted mention');
  });

  add('attachment-link', 'an attachment link in pasted markup is not rendered', () => {
    const html = attachmentFigureHTML(fileAttachment(), { caption: 'report', link: 'javascript:alert(7)' });
    expectNoExecutableDestination(T.DocumentView.render(T.HTMLParser.parse(html).getDocument()), 'pasted attachment link');
  });

  return cases;
};
