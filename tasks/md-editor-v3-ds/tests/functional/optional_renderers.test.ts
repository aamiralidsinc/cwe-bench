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
  clearInstance('katex');
  clearInstance('mermaid');
  if (mounted) unmount(mounted);
  mounted = undefined;
});

const QUIT = { noMermaid: true as const, noEcharts: true as const };
const QUIET = { noKatex: true as const, noEcharts: true as const };

it('rendered formulas keep their markup', () => {
  setInstance('katex', {
    renderToString: () => '<span class="katex-rendered">K</span>'
  });
  mounted = mountPreview({ ...QUIT, noHighlight: true, modelValue: 'see $x$ here' });
  const rendered = mounted.preview.querySelector('.katex-rendered') as HTMLElement;
  expect(rendered).toBeTruthy();
  const holder = mounted.preview.querySelector('.md-editor-katex-inline') as HTMLElement;
  expect(holder.hasAttribute('data-processed')).toBe(true);
});

it('unrendered formulas still show their source as text', () => {
  clearInstance('katex');
  mounted = mountPreview({ ...QUIT, noHighlight: true, modelValue: 'see $a^2+b^2$ here' });
  expect(mounted.preview.textContent || '').toContain('a^2+b^2');
});

it('callouts keep rendering', () => {
  mounted = mountPreview({
    ...QUIT,
    noKatex: true,
    noHighlight: true,
    modelValue: '!!! note "Heads up"\nbody\n!!!'
  });
  const block = mounted.preview.querySelector('.md-editor-admonition');
  expect(block).toBeTruthy();
  expect(mounted.preview.textContent || '').toContain('Heads up');
});

it('diagram blocks still show their source', () => {
  mounted = mountPreview({
    ...QUIET,
    noKatex: true,
    noHighlight: true,
    modelValue: '```mermaid\ngraph TD; A-->B;\n```'
  });
  const block = mounted.preview.querySelector('.md-editor-mermaid') as HTMLElement;
  expect(block).toBeTruthy();
  expect(block.textContent || '').toContain('graph TD');
});
