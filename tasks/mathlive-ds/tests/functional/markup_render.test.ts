import { convertLatexToMarkup } from '../../src/public/mathlive-ssr';
import { visibleText } from '../support/dom';

describe('HTML rendering keeps working', () => {
  test('ordinary formulas render', () => {
    for (const latex of ['\\frac{1}{2}+x^2', '\\sqrt{a+b}', '\\sum_{i=1}^n i']) {
      const output = convertLatexToMarkup(latex);
      expect(output).toContain('ML__latex');
      expect(visibleText(output).length).toBeGreaterThan(0);
    }
  });

  test('text content displays the characters that were written', () => {
    expect(visibleText(convertLatexToMarkup('\\text{hello world}'))).toBe(
      'hello world'
    );
    expect(visibleText(convertLatexToMarkup('\\text{a&b}'))).toBe('a&b');
    expect(visibleText(convertLatexToMarkup('\\text{1 < 2}'))).toBe('1 < 2');
    expect(visibleText(convertLatexToMarkup('\\text{x > y}'))).toBe('x > y');
  });

  test('a value is never encoded twice', () => {
    const output = convertLatexToMarkup('\\text{a&b}');
    expect(output).not.toContain('&amp;amp;');
  });

  test('text keeps its font and style hooks', () => {
    const output = convertLatexToMarkup('\\text{abc}\\mathit{d}');
    expect(output).toContain('ML__text');
    expect(visibleText(output)).toContain('abcd');
  });
});
