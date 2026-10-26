import { browserEnv, liveCount } from '../support/dom';

// The text a screen reader is given is produced separately from the visual output
// and the static renderer places it in the page. Its markup form must keep the
// author's characters inert while the markup it is made of stays intact.
describe('speakable rendering sink', () => {
  function render(latex: string, markup: '' | 'ssml'): any {
    const { dom, product, window } = browserEnv();
    const MFE = (globalThis as any).MathfieldElement;
    MFE.textToSpeechMarkup = markup;
    const container = window.document.createElement('div');
    dom.window.document.body.appendChild(container);
    container.textContent = `\\(${latex}\\)`;
    product.renderMathInElement(container, {
      renderAccessibleContent: 'speakable-text',
    });
    return container;
  }

  test('markup form with a closing tag', () => {
    const container = render(
      '\\text{</span><img src=x onerror=window.__pwned=1>}',
      'ssml'
    );
    expect(liveCount(container)).toBe(0);
  });

  test('markup form with a split tag', () => {
    const container = render(
      '\\text{</span><im}\\text{g src=x onerror=window.__pwned=1>}',
      'ssml'
    );
    expect(liveCount(container)).toBe(0);
  });

  test('markup form with a script element', () => {
    const container = render(
      '\\text{</span><script>window.__pwned=1</script>}',
      'ssml'
    );
    expect(liveCount(container)).toBe(0);
  });

});
