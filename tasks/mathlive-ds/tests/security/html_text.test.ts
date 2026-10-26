import { convertLatexToMarkup } from '../../src/public/mathlive-ssr';
import { liveCount, parseFragment, visibleText } from '../support/dom';

const PAYLOAD = '<img src=x onerror=window.__pwned=1>';

describe('HTML output: author text is inert', () => {
  const inputs = [
    `\\text{${PAYLOAD}}`,
    `\\mbox{${PAYLOAD}}`,
    `\\textnormal{${PAYLOAD}}`,
    `x\\text{ak${PAYLOAD}}`,
    `\\text{</span>${PAYLOAD}}`,
    `\\text{<svg onload=window.__pwned=1>}`,
  ];

  test.each(inputs)('%s', (latex) => {
    const output = convertLatexToMarkup(latex);
    expect(liveCount(parseFragment(output))).toBe(0);
  });

  test('the characters still show up as text', () => {
    const output = convertLatexToMarkup(`\\text{${PAYLOAD}}`);
    expect(visibleText(output)).toContain('<img');
  });
});
