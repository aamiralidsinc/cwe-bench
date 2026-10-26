import { XMLParser } from 'fast-xml-parser';

describe('entity processing keeps working', function () {
    it('keeps chained substitution inside a document', function () {
        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE note [
<!ENTITY nbsp "writer;">
<!ENTITY writer "Writer: Donald Duck.">
<!ENTITY copyright "Copyright: W3Schools.">
]>
<note><footer>&writer;&&nbsp;&copyright;</footer></note>`;
        const result = new XMLParser().parse(xml);
        expect(result.note.footer).toBe('Writer: Donald Duck.Writer: Donald Duck.Copyright: W3Schools.');
    });

    it('decodes numeric character references and leaves out-of-range ones alone', function () {
        const xml = `<root attr="&#9999999;">&#x1F60A;&#xFFFFFF;</root>`;
        const result = new XMLParser({ htmlEntities: true, ignoreAttributes: false }).parse(xml);
        expect(result.root['@_attr']).toBe('&#9999999;');
        expect(result.root['#text']).toBe('\u{1F60A}&#xFFFFFF;');
    });

    it('expands a small value registered by the caller and lets it override a built-in', function () {
        const parser = new XMLParser();
        parser.addEntity('brand', 'Acme');
        parser.addEntity('gt', '<>');
        const result = parser.parse('<note>&brand; &gt;last</note>');
        expect(result.note).toBe('Acme <>last');
    });

    it('keeps ordinary references and the disable switch unchanged', function () {
        const decoded = new XMLParser().parse('<root>&lt;b&gt; &amp;</root>');
        expect(decoded.root).toBe('<b> &');
        const untouched = new XMLParser({ processEntities: false }).parse('<root>&amp; &lt;</root>');
        expect(untouched.root).toBe('&amp; &lt;');
    });

    it('allows a legitimate document that stays inside the bounds', function () {
        const options = {
            processEntities: { maxTotalExpansions: 100, maxExpandedLength: 100000 },
        };
        const xml = '<!DOCTYPE d [<!ENTITY x "val"><!ENTITY price "$5.00">]>' +
            '<root>&x;&x;&x;&x;&x; &price;</root>';
        const result = new XMLParser(options).parse(xml);
        expect(result.root).toBe('valvalvalvalval $5.00');
    });
});
