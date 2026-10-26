import { XMLParser } from 'fast-xml-parser';

// A refused parse is any thrown Error; the report asks for a refusal, not a partial result.
// A replacement that is inserted literally prevents this amplification altogether, so for that one
// shape a parse that returns a proportionate value is equally acceptable.
const MAX_PROPORTIONATE_OUTPUT = 1000000;

function expectBounded(parse) {
    let value;
    try {
        value = parse();
    } catch (_) {
        return;
    }
    const text = typeof value === 'string' ? value : JSON.stringify(value);
    if (text === undefined || text.length > MAX_PROPORTIONATE_OUTPUT) {
        throw new Error(`parse returned ${text === undefined ? 'no value' : text.length + ' characters'}`);
    }
}
describe('entity processing resource bounds', function () {
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

    it('bounds growth caused by a declared replacement value', function () {
        const xml = `<!DOCTYPE d [<!ENTITY x "$'">]><root>${'&x;'.repeat(900)}${'B'.repeat(10000)}</root>`;
        expectBounded(() => new XMLParser().parse(xml));
    });

    it('applies the configured reference limit to numeric character references', function () {
        const options = {
            htmlEntities: true,
            processEntities: { maxTotalExpansions: 20 },
        };
        const xml = `<root>${'&#65;'.repeat(40)}</root>`;
        expect(() => new XMLParser(options).parse(xml)).toThrow();
    });

    it('applies the configured reference limit to the predefined entities', function () {
        const options = {
            processEntities: { maxTotalExpansions: 20 },
        };
        const xml = `<root>${'&lt;'.repeat(40)}</root>`;
        expect(() => new XMLParser(options).parse(xml)).toThrow();
    });

    it('bounds references to a value made available by the caller', function () {
        expect(() => {
            const parser = new XMLParser();
            parser.addEntity('big', 'B'.repeat(200000));
            return parser.parse(`<root>${'&big;'.repeat(50)}</root>`);
        }).toThrow();
    });
});
