import { convertLatexToMathMl } from '../../src/public/mathlive-ssr';
import { xmlIsWellFormed } from '../support/dom';

describe('serialized math output: delimiters are encoded', () => {
  const inputs = [
    '\\left<x\\right>',
    '\\bigl<x\\bigr>',
    '\\left<x\\right|',
    '\\left< x \\right.',
    '\\left<\\frac{1}{2}\\right>',
  ];

  test.each(inputs)('%s', (latex) => {
    const output = convertLatexToMathMl(latex);
    expect(xmlIsWellFormed(`<math>${output}</math>`)).toBe(true);
  });
});
