import { browserEnv, liveCount } from '../support/dom';

// When a formula cannot be rendered, the static element displays the original
// content. That content is text supplied by the page author and must stay inert.
describe('static element fallback content', () => {
  test('unrenderable formula keeps its content as text', async () => {
    const { dom, window } = browserEnv();
    const element = window.document.createElement('math-span');
    element.textContent =
      '\\(\\href{javascript:alert(1)}{<img src=x onerror=window.__pwned=1>}\\)';
    dom.window.document.body.appendChild(element);
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(element.shadowRoot).toBeTruthy();
    expect(liveCount(element.shadowRoot)).toBe(0);
  });
});
