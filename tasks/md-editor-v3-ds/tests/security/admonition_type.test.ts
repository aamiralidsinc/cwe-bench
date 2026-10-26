import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, QUIET, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  if (mounted) unmount(mounted);
  mounted = undefined;
});

it('callout kind metadata stays data', () => {
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    modelValue: '!!! x"><img/src=x\nbody\n!!!'
  });
  expect(mounted.preview.querySelectorAll('img,script,iframe,object,embed').length).toBe(0);
});
