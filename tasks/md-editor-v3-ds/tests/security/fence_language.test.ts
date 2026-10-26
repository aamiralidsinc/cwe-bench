import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, QUIET, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  if (mounted) unmount(mounted);
  mounted = undefined;
});

// Values a document author can put in a fenced block's info string (no whitespace).
const MARKUP = 'img,script,iframe,object,embed';

it('quoted fence metadata stays data', () => {
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    modelValue: '```a"><img/src=x>\nbody\n```'
  });
  expect(mounted.preview.querySelectorAll(MARKUP).length).toBe(0);
});

it('an unquoted fence metadata attribute stays data', () => {
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    modelValue: '```a><img/src=x\nbody\n```'
  });
  expect(mounted.preview.querySelectorAll(MARKUP).length).toBe(0);
});

it('fence metadata in a tab group stays data', () => {
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    modelValue: '```a"><img/src=x [grp]\nbody\n```'
  });
  expect(mounted.preview.querySelectorAll(MARKUP).length).toBe(0);
});
