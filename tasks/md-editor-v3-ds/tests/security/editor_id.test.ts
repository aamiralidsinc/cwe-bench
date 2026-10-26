import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, QUIET, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  delete (window as Record<string, unknown>).__mdPwn;
  delete (window as Record<string, unknown>).__mdPwn2;
  if (mounted) unmount(mounted);
  mounted = undefined;
});

const TABS = '```js [grp]\nbody\n```\n\n```ts [grp]\nmore\n```';

/** Run a rendered inline handler the way the HTML parser would. */
const runInline = (source: string, element: Element) => {
  try {
    new Function('event', source).call(element, new MouseEvent('click'));
  } catch {
    /* a handler that throws is still not an injected one */
  }
};

it('an instance identifier cannot execute as script', () => {
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    editorId: "e1');window.__mdPwn=1;//",
    modelValue: TABS
  });
  const label = mounted.preview.querySelector('label[onclick]') as HTMLElement | null;
  if (label) runInline(label.getAttribute('onclick') || '', label);
  expect((window as Record<string, unknown>).__mdPwn).toBeUndefined();
  expect(mounted.preview.querySelectorAll('img,script,iframe,object,embed').length).toBe(0);
});

it('an instance identifier cannot add attributes to the markup', () => {
  mounted = mountPreview({
    ...QUIET,
    noHighlight: true,
    editorId: 'e2" onmouseover="window.__mdPwn2=1',
    modelValue: TABS
  });
  expect(mounted.preview.querySelectorAll('[onmouseover]').length).toBe(0);
});
