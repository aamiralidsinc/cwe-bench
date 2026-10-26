import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, QUIET, type Mounted } from '../support/helpers';

const TABS = '```js [grp]\nbody\n```\n\n```ts [grp]\nmore\n```';
const mountedList: Mounted[] = [];

afterEach(() => {
  while (mountedList.length) unmount(mountedList.pop()!);
});

const runInline = (label: HTMLElement) => {
  const source = label.getAttribute('onclick');
  if (source) {
    new Function('event', source).call(label, new MouseEvent('click'));
  } else {
    label.click();
  }
};

it('separate editor instances keep separate tab groups', () => {
  const a = mountPreview({ ...QUIET, noHighlight: true, editorId: 'editor-one', modelValue: TABS });
  const b = mountPreview({ ...QUIET, noHighlight: true, editorId: 'editor-two', modelValue: TABS });
  mountedList.push(a, b);
  const names = (m: Mounted) =>
    Array.from(m.preview.querySelectorAll('input[type=radio]')).map(
      (i) => (i as HTMLInputElement).name
    );
  const namesA = names(a);
  const namesB = names(b);
  expect(namesA.length).toBeGreaterThan(0);
  expect(namesA.length).toBe(namesB.length);
  expect(namesA.some((n) => namesB.includes(n))).toBe(false);
});

it('a tab label still selects its panel', () => {
  const m = mountPreview({ ...QUIET, noHighlight: true, editorId: 'editor-tabs', modelValue: TABS });
  mountedList.push(m);
  const labels = m.preview.querySelectorAll('ul.md-editor-codetab-label label');
  expect(labels.length).toBe(2);
  const second = labels[1] as HTMLElement;
  const target = m.preview.querySelector(`#${second.getAttribute('for')}`);
  expect(target).toBeTruthy();
  runInline(second);
  const panels = m.preview.querySelectorAll('div[role="tabpanel"] input[type=radio]');
  expect(panels.length).toBe(2);
  expect((panels[1] as HTMLInputElement).checked).toBe(true);
});
