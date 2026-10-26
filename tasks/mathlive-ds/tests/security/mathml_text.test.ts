import { convertLatexToMathMl } from '../../src/public/mathlive-ssr';
import { liveCount, parseFragment } from '../support/dom';

const PAYLOAD = '<img src=x onerror=window.__pwned=1>';

describe('serialized math output: author text is inert', () => {
  const inputs = [
    `\\text{${PAYLOAD}}`,
    `\\textnormal{${PAYLOAD}}`,
    `\\textrm{${PAYLOAD}}`,
    `\\colorbox{red}{${PAYLOAD}}`,
    `x^{\\text{${PAYLOAD}}}`,
    `\\sqrt{\\text{${PAYLOAD}}}`,
    `\\frac{\\text{${PAYLOAD}}}{2}`,
    // Two adjacent text atoms are serialized as one run.
    `\\text{<im}\\text{g src=x onerror=window.__pwned=1>}`,
    `\\text{a}\\text{${PAYLOAD}}`,
  ];

  test.each(inputs)('%s', (latex) => {
    const output = convertLatexToMathMl(latex);
    expect(liveCount(parseFragment(output))).toBe(0);
  });
});
