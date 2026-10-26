import { afterEach, expect, it } from 'vitest';
import { mountPreview, setEnglishText, unmount, QUIET, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  if (mounted) unmount(mounted);
  mounted = undefined;
});

it('copy feedback cannot add attributes to the block', () => {
  setEnglishText({ text: 'COPY" onmouseover="window.__tips=1', successTips: 'OK', failTips: 'BAD' });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    modelValue: '```js\nbody\n```'
  });
  expect(mounted.preview.querySelectorAll('[onmouseover]').length).toBe(0);
});

it('copy feedback cannot add elements to the block', () => {
  setEnglishText({ text: '<img data-xt1=1>', successTips: 'OK', failTips: 'BAD' });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    modelValue: '```js\nbody\n```'
  });
  const button = mounted.preview.querySelector('.md-editor-copy-button') as HTMLElement;
  expect(button).toBeTruthy();
  expect(mounted.preview.querySelectorAll('[data-xt1]').length).toBe(0);
});

it('copy feedback in a tab group cannot add elements', () => {
  setEnglishText({ text: '<img data-xt2=1>', successTips: 'OK', failTips: 'BAD' });
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    language: 'en-US',
    modelValue: '```js [grp]\nbody\n```\n\n```ts [grp]\nmore\n```'
  });
  expect(mounted.preview.querySelectorAll('[data-xt2]').length).toBe(0);
});
