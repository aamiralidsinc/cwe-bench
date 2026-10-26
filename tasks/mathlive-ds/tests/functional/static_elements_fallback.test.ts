import { browserEnv } from '../support/dom';

// A formula that cannot be rendered is still shown to the reader. The fallback must
// keep displaying the original content rather than becoming empty.
describe('static element error display', () => {
  test('unrenderable content is still displayed', async () => {
    const { dom, window } = browserEnv();
    const element = window.document.createElement('math-span');
    const source = '\\(\\href{javascript:alert(1)}{x+1}\\)';
    element.textContent = source;
    dom.window.document.body.appendChild(element);
    await new Promise((resolve) => setTimeout(resolve, 10));
    const fallback = element.shadowRoot.querySelector('[part="error"]');
    expect(fallback).toBeTruthy();
    expect(fallback.textContent).toContain('x+1');
    expect(fallback.style.display).not.toBe('none');
  });
});
