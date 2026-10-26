'use strict';

/*
 * Security cases: entity resolution must use an entity's name literally, and declared replacement
 * text must be inserted literally. Each case drives the library's public API and either throws
 * (a rejection counts as blocked) or checks the returned value against a literal written here.
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

function registeredName(XMLParser, id, key, reference, marker, where) {
  return {
    classname: 'security/name-confusion',
    name: `${id}: a registered entity must not answer the reference in ${where}`,
    run() {
      const parser = new XMLParser();
      try {
        parser.addEntity(key, marker);
      } catch (e) {
        return; // the name was refused: blocked
      }
      let value;
      try {
        value = parser.parse(`<note>${reference}</note>`).note;
      } catch (e) {
        return; // refused: blocked
      }
      if (asText(value).indexOf(marker) !== -1) {
        throw new Error(`a reference with a different name resolved to the registered entity: ${asText(value).slice(0, 200)}`);
      }
    },
  };
}

function literalInsertion(XMLParser, id, makeParser, xml, expected) {
  return {
    classname: 'security/literal-value',
    name: `${id}: declared text appears exactly as written`,
    run() {
      let value;
      try {
        value = makeParser().parse(xml).note;
      } catch (e) {
        throw new Error(`a document with legitimate text was refused: ${e && e.message}`);
      }
      if (value !== expected) {
        throw new Error(`got ${JSON.stringify(value)}, expected ${JSON.stringify(expected)}`);
      }
    },
  };
}

module.exports = function (XMLParser) {
  const cases = [];

  // T1 - a name accepted by the document-declaration grammar must be consumed literally when the
  // parser builds the matcher for that entity's references.
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

  // T2 - the same operation when the entity is defined by the application rather than by the
  // parsed document.
  cases.push(registeredName(
    XMLParser, 'T2-registered-dot', 'a.b', '&aZb;', 'NCMARK5',
    'a text node (registered name containing a dot)'));
  cases.push(registeredName(
    XMLParser, 'T2-registered-plus', 'a+b', '&aab;', 'NCMARK6',
    'a text node (registered name containing a plus)'));

  // T3 - the declared text is data. Special characters in it must be inserted as written, not
  // interpreted by the substitution step.
  cases.push(literalInsertion(
    XMLParser, 'T3-doctype-suffix',
    () => new XMLParser(),
    '<!DOCTYPE note [<!ENTITY x "$\'">]><note>PRE&x;POST</note>',
    "PRE$'POST"));
  cases.push(literalInsertion(
    XMLParser, 'T3-doctype-dollar',
    () => new XMLParser(),
    '<!DOCTYPE note [<!ENTITY x "$$">]><note>PRE&x;POST</note>',
    'PRE$$POST'));
  cases.push(literalInsertion(
    XMLParser, 'T3-registered-suffix',
    () => {
      const parser = new XMLParser();
      parser.addEntity('x', "$'");
      return parser;
    },
    '<note>PRE&x;POST</note>',
    "PRE$'POST"));

  return cases;
};
