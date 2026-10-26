import { afterEach, expect, it, vi } from 'vitest';
import { mountPreview, setEnglishText, unmount, QUIET, type Mounted } from '../support/helpers';

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

it('copy result feedback is shown as text', async () => {
  vi.useFakeTimers();
  setEnglishText({
    text: 'COPY',
    successTips: '<img data-ok=1>OK',
    failTips: '<img data-bad=1>BAD'
  });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    modelValue: '```js\nbody\n```'
  });
  const button = mounted.preview.querySelector('.md-editor-copy-button') as HTMLElement;
  button.click();
  await settle();
  expect(mounted.preview.querySelectorAll('[data-ok],[data-bad]').length).toBe(0);
  expect(button.textContent).toMatch(/OK|BAD/);
});

it('the restored copy label is shown as text', async () => {
  vi.useFakeTimers();
  setEnglishText({ text: '<img data-restore=1>', successTips: 'OK', failTips: 'BAD' });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    modelValue: '```js\nbody\n```'
  });
  const button = mounted.preview.querySelector('.md-editor-copy-button') as HTMLElement;
  button.click();
  await settle();
  vi.advanceTimersByTime(2000);
  await settle();
  expect(mounted.preview.querySelectorAll('[data-restore]').length).toBe(0);
});
