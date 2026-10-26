'use strict';

/*
 * Payload builders and the destination predicate shared by the hidden cases. Everything here is
 * bookkeeping for the tests: payloads are literals and the predicate is written out, never
 * derived from the product under test.
 */

// Schemes that a browser will treat as code when a rendered link is followed. The value is
// normalised the way a browser's URL parser ignores control characters and spaces before the
// scheme, then matched case-insensitively.
function isExecutableDestination(value) {
  const normalised = String(value)
    .replace(/[\u0000- \u007f]+/g, '')
    .toLowerCase();
  return (
    normalised.startsWith('javascript:') ||
    normalised.startsWith('vbscript:') ||
    normalised.startsWith('data:')
  );
}

function executableDestinations(element) {
  return Array.from(element.querySelectorAll('[href]'))
    .map((node) => node.getAttribute('href'))
    .filter(isExecutableDestination);
}

function expectNoExecutableDestination(element, label) {
  const found = executableDestinations(element);
  if (found.length) {
    throw new Error(`${label}: rendered ${JSON.stringify(found)}`);
  }
}

function stringBlock(string, attributes, blockAttributes = [], htmlAttributes = {}) {
  return { text: [ { type: 'string', string, attributes } ], attributes: blockAttributes, htmlAttributes };
}

function textDocument(string, attributes) {
  return JSON.stringify([ stringBlock(string, attributes) ]);
}

function attachmentBlock(pieceAttributes, attachment) {
  return JSON.stringify([ {
    text: [ { type: 'attachment', attachment, attributes: pieceAttributes } ],
    attributes: [],
    htmlAttributes: {},
  } ]);
}

function fileAttachment(extra = {}) {
  return { id: 'attachment-1', contentType: 'application/pdf', filename: 'report.pdf', filesize: 10, ...extra };
}

function renderJSON(T, json) {
  const document = T.deserializeFromContentType(json, 'application/json');
  return T.DocumentView.render(document);
}

function renderModel(T, document) {
  return T.DocumentView.render(document);
}

// The JSON block markup used by the project's document format when a figure carries extra
// piece attributes next to its attachment JSON.
function attachmentFigureHTML(attachment, pieceAttributes) {
  const quote = (value) => JSON.stringify(value).replace(/"/g, '&quot;');
  return `<div><figure data-trix-attachment="${quote(attachment)}" data-trix-attributes="${quote(pieceAttributes)}"></figure></div>`;
}

module.exports = {
  isExecutableDestination,
  executableDestinations,
  expectNoExecutableDestination,
  stringBlock,
  textDocument,
  attachmentBlock,
  fileAttachment,
  renderJSON,
  renderModel,
  attachmentFigureHTML,
};
