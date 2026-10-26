import { convertLatexToMathMl } from '../../src/public/mathlive-ssr';
import { visibleText } from '../support/dom';

function text(latex: string): string {
  return visibleText(`<math>${convertLatexToMathMl(latex)}</math>`);
}

describe('serialized math keeps symbols and delimiters working', () => {
  test('named symbols still produce their character', () => {
    expect(text('\\alpha')).toBe('\u03b1');
    expect(text('\\Gamma')).toBe('\u0393');
    expect(text('\\infty')).toBe('\u221e');
    expect(text('\\sum_{i=1}^{n}')).toContain('\u2211');
  });

  test('characters written directly still produce themselves', () => {
    expect(text('\u03b1')).toBe('\u03b1');
    expect(text('\u00e9')).toBe('\u00e9');
  });

  test('text values display the characters that were written', () => {
    expect(text('\\text{a&b}')).toBe('a&b');
    expect(text('\\text{1 < 2}')).toBe('1 < 2');
  });

  test('delimiters keep their identifiable form', () => {
    expect(text('\\left(x\\right)')).toContain('(');
    expect(text('\\left(x\\right)')).toContain(')');
    expect(text('\\left|x\\right.')).toContain('|');
    expect(text('\\left\\{x\\right\\}')).toContain('{');
  });

  test('operator arguments still render', () => {
    expect(text('\\operatorname*{\\text{lim}}')).toContain('lim');
    expect(text('\\operatorname{arg}')).toContain('arg');
  });

  test('structures still render', () => {
    expect(convertLatexToMathMl('\\frac{1}{2}')).toContain('<mfrac>');
    expect(convertLatexToMathMl('\\sqrt{x}')).toContain('<msqrt>');
    expect(convertLatexToMathMl('x^2')).toContain('<msup>');
  });
});
