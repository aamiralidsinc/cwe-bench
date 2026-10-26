'use strict';

/*
 * Security cases reached through the editor's stored-document API: a document that the host
 * application loads, or that the editor restores from a saved snapshot, is deserialised and
 * rendered. Every case asserts that no value supplied by the document becomes an executable
 * destination on a rendered link.
 */

const {
  textDocument,
  attachmentBlock,
  fileAttachment,
  renderJSON,
  expectNoExecutableDestination,
} = require('../support/checks');

module.exports = function ({ T }) {
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: `security/stored-document/${id}`, name, run });

  add('link-plain', 'a script destination in a stored link is not rendered', () => {
    const element = renderJSON(T, textDocument('Click me', { href: 'javascript:alert(1)' }));
    expectNoExecutableDestination(element, 'stored link');
  });

  add('link-mixed-case', 'a mixed-case script destination in a stored link is not rendered', () => {
    const element = renderJSON(T, textDocument('Click me', { href: 'JaVaScRiPt:alert(1)' }));
    expectNoExecutableDestination(element, 'mixed-case stored link');
  });

  add('link-leading-space', 'a whitespace-padded script destination in a stored link is not rendered', () => {
    const element = renderJSON(T, textDocument('Click me', { href: '   javascript:alert(1)' }));
    expectNoExecutableDestination(element, 'whitespace-padded stored link');
  });

  add('link-non-string', 'a script destination carried as a non-string value is not rendered', () => {
    const element = renderJSON(T, textDocument('Click me', { href: [ 'javascript:alert(1)' ] }));
    expectNoExecutableDestination(element, 'non-string stored link');
  });

  add('link-document-api', 'a script destination is not rendered through the document deserialiser', () => {
    const document = T.Document.fromJSONString(textDocument('Click me', { href: 'javascript:alert(2)' }));
    const element = T.DocumentView.render(document);
    expectNoExecutableDestination(element, 'document deserialiser');
  });

  add('mention', 'a mention destination with a script value is not rendered', () => {
    const element = renderJSON(T, textDocument('@alex', { mention: 'javascript:alert(3)' }));
    expectNoExecutableDestination(element, 'stored mention');
  });

  add('attachment-link', 'an attachment link with a script value is not rendered', () => {
    const element = renderJSON(
      T,
      attachmentBlock({ caption: 'report', link: 'javascript:alert(4)' }, fileAttachment()),
    );
    expectNoExecutableDestination(element, 'stored attachment link');
  });

  add('attachment-link-non-string', 'an attachment link carried as a non-string value is not rendered', () => {
    const element = renderJSON(
      T,
      attachmentBlock({ link: [ 'javascript:alert(5)' ] }, fileAttachment()),
    );
    expectNoExecutableDestination(element, 'non-string stored attachment link');
  });

  return cases;
};
