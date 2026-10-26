import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  if (mounted) unmount(mounted);
  mounted = undefined;
});

it('ordinary markdown renders as before', () => {
  mounted = mountPreview({
    noKatex: true,
    noMermaid: true,
    noEcharts: true,
    noHighlight: true,
    modelValue: '# Title\n\n- one\n- two\n\n> quote'
  });
  expect(mounted.preview.querySelector('h1')?.textContent).toBe('Title');
  expect(mounted.preview.querySelectorAll('li').length).toBe(2);
  expect(mounted.preview.querySelector('blockquote')).toBeTruthy();
});

it('a code block renders its language label and content', () => {
  mounted = mountPreview({
    noKatex: true,
    noMermaid: true,
    noEcharts: true,
    noHighlight: true,
    modelValue: '```javascript\nconst a = 1;\n```'
  });
  const code = mounted.preview.querySelector('pre code') as HTMLElement;
  expect(code.className).toContain('language-javascript');
  expect(code.textContent).toContain('const a = 1;');
  expect(mounted.preview.querySelector('.md-editor-code-lang')?.textContent).toBe(
    'javascript'
  );
});
