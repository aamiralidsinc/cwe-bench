import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, QUIET, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  if (mounted) unmount(mounted);
  mounted = undefined;
});

it('unrendered formula source stays text', () => {
  mounted = mountPreview({
    noMermaid: true,
    noEcharts: true,
    noHighlight: true,
    modelValue: 'inline $<img data-kx1=1>x$ end'
  });
  expect(mounted.preview.querySelectorAll('[data-kx1]').length).toBe(0);
  expect(mounted.preview.textContent || '').toContain('data-kx1');
});

it('unrendered block formula source stays text', () => {
  mounted = mountPreview({
    noMermaid: true,
    noEcharts: true,
    noHighlight: true,
    modelValue: '$$\n<img data-kx2=1>x\n$$'
  });
  expect(mounted.preview.querySelectorAll('[data-kx2]').length).toBe(0);
});
