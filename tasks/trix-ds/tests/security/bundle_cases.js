'use strict';

/*
 * Security cases reached through the prebuilt asset that ships with the repository for
 * server-side applications. It exposes the same document API as the source package, so the same
 * property applies to a document it renders.
 */

const { textDocument, expectNoExecutableDestination } = require('../support/checks');

module.exports = function ({ Trix }) {
  const cases = [];
  const add = (id, name, run) => cases.push({ classname: `security/prebuilt-asset/${id}`, name, run });

  const render = (json) => Trix.views.DocumentView.render(Trix.Document.fromJSONString(json));

  add('link', 'a script destination in a document loaded through the shipped asset is not rendered', () => {
    expectNoExecutableDestination(render(textDocument('Click me', { href: 'javascript:alert(8)' })), 'shipped asset link');
  });

  add('link-mixed-case', 'a mixed-case script destination through the shipped asset is not rendered', () => {
    expectNoExecutableDestination(render(textDocument('Click me', { href: 'JavaScript:alert(8)' })), 'shipped asset mixed-case link');
  });

  return cases;
};
