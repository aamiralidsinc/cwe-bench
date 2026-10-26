import { afterEach, expect, it, vi } from 'vitest';
import {
  mountPreview,
  setEnglishText,
  unmount,
  QUIET,
  type Mounted
} from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  vi.useRealTimers();
  if (mounted) unmount(mounted);
  mounted = undefined;
});

const settle = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

it('the copy control shows the configured label and reports the result', async () => {
  vi.useFakeTimers();
  const copied: string[] = [];
  setEnglishText({ text: 'COPY', successTips: 'OK', failTips: 'BAD' });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    formatCopiedText: (text: string) => {
      copied.push(text);
      return text;
    },
    modelValue: '```js\nconst a = 1;\n```'
  });
  const button = mounted.preview.querySelector('.md-editor-copy-button') as HTMLElement;
  expect(button.textContent).toBe('COPY');
  expect(button.getAttribute('data-tips')).toBe('COPY');
  button.click();
  await settle();
  expect(copied.join('')).toContain('const a = 1;');
  expect(['OK', 'BAD']).toContain(button.textContent);
  expect(button.children.length).toBe(0);
  vi.advanceTimersByTime(2000);
  await settle();
  expect(button.textContent).toBe('COPY');
});

it('a configured copy icon is kept as markup', async () => {
  vi.useFakeTimers();
  setEnglishText({ text: 'COPY', successTips: 'OK', failTips: 'BAD' });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    customIcon: { copy: '<svg data-icon="copy"></svg>' },
    modelValue: '```js\nbody\n```'
  });
  const button = mounted.preview.querySelector('.md-editor-copy-button') as HTMLElement;
  expect(button.querySelector('svg[data-icon="copy"]')).toBeTruthy();
  expect(button.getAttribute('data-tips')).toBe('COPY');
  button.click();
  await settle();
  expect(button.querySelector('svg[data-icon="copy"]')).toBeTruthy();
  expect(['OK', 'BAD']).toContain(button.getAttribute('data-tips'));
});
