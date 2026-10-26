import { afterEach, expect, it } from 'vitest';
import {
  clearInstance,
  mountPreview,
  setInstance,
  unmount,
  type Mounted
} from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  clearInstance('highlight');
  if (mounted) unmount(mounted);
  mounted = undefined;
});

const QUIT = { noKatex: true, noMermaid: true, noEcharts: true };

it('language names with punctuation keep their code class', () => {
  mounted = mountPreview({ ...QUIT, modelValue: '```c++\nint x;\n```' });
  const code = mounted.preview.querySelector('pre code') as HTMLElement;
  expect(code).toBeTruthy();
  expect(code.className).toContain('language-c++');
});

it('a language name with a sharp keeps its code class', () => {
  mounted = mountPreview({ ...QUIT, modelValue: '```c#\nint x;\n```' });
  const code = mounted.preview.querySelector('pre code') as HTMLElement;
  expect(code.className).toContain('language-c#');
});

it('highlighter markup is preserved in the preview', () => {
  setInstance('highlight', {
    getLanguage: (lang: string) => (lang === 'js' ? {} : null),
    highlight: () => ({ value: '<span class="hljs-keyword">HL</span>' })
  });
  mounted = mountPreview({ ...QUIT, modelValue: '```js\nconst a = 1;\n```' });
  const span = mounted.preview.querySelector('pre code span.hljs-keyword') as HTMLElement;
  expect(span).toBeTruthy();
  expect(span.textContent).toBe('HL');
});

it('plain code is still shown when highlighting is off', () => {
  mounted = mountPreview({ ...QUIT, noHighlight: true, modelValue: '```js\nconst a = 1;\n```' });
  const code = mounted.preview.querySelector('pre code') as HTMLElement;
  expect(code.textContent).toContain('const a = 1;');
});
