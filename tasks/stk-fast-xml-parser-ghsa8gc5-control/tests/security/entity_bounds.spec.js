import { XMLParser } from 'fast-xml-parser';

// A refused parse is any thrown Error; the report asks for a refusal, not a partial result.
describe('declared entity expansion is bounded', function () {
    it('bounds a declared entity referenced many times in element text', function () {
        const value = 'A'.repeat(5000);
        const xml = `<!DOCTYPE foo [<!ENTITY big "${value}">]><root>${'&big;'.repeat(2000)}</root>`;
        expect(() => new XMLParser().parse(xml)).toThrow();
    });

    it('bounds a declared entity referenced many times in an attribute', function () {
        const value = 'A'.repeat(5000);
        const xml = `<!DOCTYPE foo [<!ENTITY big "${value}">]><root attr="${'&big;'.repeat(2000)}"/>`;
        expect(() => new XMLParser({ ignoreAttributes: false }).parse(xml)).toThrow();
    });

    it('honours a configured reference limit', function () {
        const options = { processEntities: { maxTotalExpansions: 50 } };
        const xml = `<!DOCTYPE foo [<!ENTITY e "0123456789">]><root>${'&e;'.repeat(100)}</root>`;
        expect(() => new XMLParser(options).parse(xml)).toThrow();
    });

    it('bounds accumulated growth even below the reference count', function () {
        const value = 'A'.repeat(5000);
        const xml = `<!DOCTYPE foo [<!ENTITY big "${value}">]><root>${'&big;'.repeat(500)}</root>`;
        expect(() => new XMLParser().parse(xml)).toThrow();
    });
});
