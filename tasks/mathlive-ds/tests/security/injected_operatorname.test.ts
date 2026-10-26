import { convertLatexToMathMl } from '../../src/public/mathlive-ssr';
import { liveCount, parseFragment } from '../support/dom';

// A starred operator renders the characters of its argument.
describe('operator argument content is inert', () => {
  const inputs = [
    '\\operatorname*{\\text{<img src=x onerror=window.__pwned=1>}}',
    '\\operatorname*{\\text{a<img src=x onerror=window.__pwned=1>}}',
  ];

  test.each(inputs)('%s', (latex) => {
    const output = convertLatexToMathMl(latex);
    expect(liveCount(parseFragment(output))).toBe(0);
  });
});
