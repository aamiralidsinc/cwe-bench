import { afterEach, expect, it } from 'vitest';
import { mountPreview, unmount, QUIET, type Mounted } from '../support/helpers';

let mounted: Mounted | undefined;
afterEach(() => {
  if (mounted) unmount(mounted);
  mounted = undefined;
});

it('an unrendered diagram source stays data', () => {
  mounted = mountPreview({
    noKatex: true,
    noEcharts: true,
    noHighlight: true,
    modelValue: '```mermaid\n"><img/src=x>\n```'
  });
  expect(mounted.preview.querySelectorAll('img,script,iframe,object,embed').length).toBe(0);
});
