'use strict';

/*
 * Control security cases (the advisory route only): a document-declared entity name must be
 * consumed literally when the parser builds the matcher for that entity's references. Each case
 * drives the library's public API and either throws (a rejection counts as blocked) or checks the
 * returned value.
 */

function asText(value) {
  return typeof value === 'string' ? value : JSON.stringify(value);
}

function unrelatedReference(XMLParser, id, xml, options, marker, where) {
  return {
    classname: 'security/name-confusion',
    name: `${id}: a declaration must not answer the reference in ${where}`,
    run() {
      let value;
      try {
        value = new XMLParser(options).parse(xml).note;
      } catch (e) {
        return; // refused: blocked
      }
      if (asText(value).indexOf(marker) !== -1) {
        throw new Error(`the parsed value contains text declared under a different entity name: ${asText(value).slice(0, 200)}`);
      }
    },
  };
}

module.exports = function (XMLParser) {
  const cases = [];

  cases.push(unrelatedReference(
    XMLParser, 'T1-doctype-text',
    '<!DOCTYPE note [<!ENTITY a\\ "NCMARK1">]><note>&a;</note>',
    undefined, 'NCMARK1', 'a text node'));
  cases.push(unrelatedReference(
    XMLParser, 'T1-doctype-attribute',
    '<!DOCTYPE note [<!ENTITY a\\ "NCMARK2">]><note attr="&a;"/>',
    { ignoreAttributes: false }, 'NCMARK2', 'an attribute value'));
  cases.push(unrelatedReference(
    XMLParser, 'T1-doctype-nested',
    '<!DOCTYPE note [<!ENTITY x\\ "NCMARK3">]><note><body>&x;</body></note>',
    undefined, 'NCMARK3', 'a nested element'));
  cases.push(unrelatedReference(
    XMLParser, 'T1-doctype-alongside',
    '<!DOCTYPE note [<!ENTITY b\\ "NCMARK4"><!ENTITY ok "fine">]><note>&b; and &ok;</note>',
    undefined, 'NCMARK4', 'a document that also declares an ordinary entity'));

  return cases;
};
