'use strict';

/*
 * Functional cases: legitimate documents and registered entities must keep resolving exactly as
 * today, including the values coupled to each protected operation. Expected values are literals.
 */

function asValue(v) {
  return JSON.stringify(v);
}

function expectedCase(XMLParser, id, makeParser, xml, pick, expected, what) {
  return {
    classname: 'functional/entities',
    name: `${id}: ${what}`,
    run() {
      const got = pick(makeParser().parse(xml));
      if (asValue(got) !== asValue(expected)) {
        throw new Error(`got ${asValue(got)}, expected ${asValue(expected)}`);
      }
    },
  };
}

module.exports = function (XMLParser) {
  const cases = [];
  const note = r => r.note;

  cases.push(expectedCase(XMLParser, 'F-doctype-text',
    () => new XMLParser(),
    '<!DOCTYPE note [<!ENTITY aa "OK">]><note>&aa;</note>',
    note, 'OK', 'an ordinary declared entity expands in text'));

  cases.push(expectedCase(XMLParser, 'F-doctype-attribute',
    () => new XMLParser({ ignoreAttributes: false }),
    '<!DOCTYPE note [<!ENTITY aa "OK">]><note attr="&aa;"/>',
    note, { '@_attr': 'OK' }, 'an ordinary declared entity expands in an attribute'));

  cases.push(expectedCase(XMLParser, 'F-doctype-value-space',
    () => new XMLParser(),
    '<!DOCTYPE note [<!ENTITY name "A B">]><note>&name;</note>',
    note, 'A B', 'declared text may contain a space'));

  cases.push(expectedCase(XMLParser, 'F-dynamic-chain',
    () => new XMLParser(),
    '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE note [<!ENTITY nbsp "writer;"><!ENTITY writer "Writer: Donald Duck."><!ENTITY copyright "Copyright: W3Schools.">]><note><footer>&writer;&&nbsp;&copyright;</footer></note>',
    r => r.note.footer,
    'Writer: Donald Duck.Writer: Donald Duck.Copyright: W3Schools.',
    'the documented dynamic expansion still works'));

  cases.push(expectedCase(XMLParser, 'F-registered-plain',
    () => {
      const p = new XMLParser();
      p.addEntity('brand', 'Acme');
      return p;
    },
    '<note>&brand; is here</note>',
    note, 'Acme is here', 'an application-registered entity resolves'));

  cases.push(expectedCase(XMLParser, 'F-registered-dot',
    () => {
      const p = new XMLParser();
      p.addEntity('a.b', 'OK');
      return p;
    },
    '<note>&a.b;</note>',
    note, 'OK', 'a registered name containing a dot still resolves'));

  cases.push(expectedCase(XMLParser, 'F-registered-hash',
    () => {
      const p = new XMLParser();
      p.addEntity('#xD', ' ');
      return p;
    },
    '<note>a&#xD;b</note>',
    note, 'a b', 'the documented #xD registration still resolves'));

  cases.push(expectedCase(XMLParser, 'F-registered-override',
    () => {
      const p = new XMLParser();
      p.addEntity('gt', '<>');
      return p;
    },
    '<note>&gt;last</note>',
    note, '<>last', 'a registered entity may override a predefined one'));

  cases.push(expectedCase(XMLParser, 'F-registered-dollar',
    () => {
      const p = new XMLParser();
      p.addEntity('price', '$5.00');
      return p;
    },
    '<note>&price;</note>',
    note, '$5.00', 'a registered value containing a currency sign stays literal'));

  cases.push(expectedCase(XMLParser, 'F-doctype-dollar',
    () => new XMLParser(),
    '<!DOCTYPE note [<!ENTITY x "$5.00">]><note>&x;</note>',
    note, '$5.00', 'a declared value containing a currency sign stays literal'));

  cases.push(expectedCase(XMLParser, 'F-amp-lt',
    () => new XMLParser(),
    '<note>&amp;lt;</note>',
    note, '&lt;', 'a double-escaped reference decodes once'));

  cases.push(expectedCase(XMLParser, 'F-unknown-reference',
    () => new XMLParser(),
    '<note>&unknown;</note>',
    note, '&unknown;', 'an undeclared reference is left as written'));

  cases.push(expectedCase(XMLParser, 'F-multiple-references',
    () => new XMLParser(),
    '<!DOCTYPE note [<!ENTITY w "ab">]><note>&w;&w;</note>',
    note, 'abab', 'an entity reference may appear several times'));

  cases.push(expectedCase(XMLParser, 'F-processing-off',
    () => new XMLParser({ processEntities: false }),
    '<note>&lt;</note>',
    note, '&lt;', 'entity processing can still be turned off'));

  return cases;
};
