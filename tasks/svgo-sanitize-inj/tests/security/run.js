'use strict';
// Security suite: every case feeds an attacker-crafted document through the
// opt-in sanitation pass and asserts the executable construct is neutralized.
// Each case fails on the vulnerable tree and passes only on a correct fix.
// A unique marker (XSSPROBE) stands in for the script body a browser would run;
// if any executable construct survives, the marker survives with it.
const path = require('path');
const { runSuite } = require('../support/runner.js');

const NS = 'xmlns="http://www.w3.org/2000/svg"';
const M = 'XSSPROBE';

const cases = [
  {
    name: 'an inline event-handler attribute does not survive sanitation',
    run: ({ sanitize, refuteContains }) => {
      const out = sanitize(`<svg ${NS}><rect onclick="${M}()"/></svg>`);
      refuteContains(out, 'onclick', 'event-handler attribute must be removed');
      refuteContains(out, M, 'the handler body must be gone');
    },
  },
  {
    name: 'a link whose target executes code is neutralized',
    run: ({ sanitize, refuteContains }) => {
      const out = sanitize(`<svg ${NS}><a href="javascript:${M}()"><rect/></a></svg>`);
      refuteContains(out, 'javascript:', 'executable link scheme must not remain');
      refuteContains(out, M, 'the link payload must be gone');
    },
  },
  {
    name: 'embedded HTML carrying an active document is stripped',
    run: ({ sanitize, refuteContains }) => {
      const out = sanitize(
        `<svg ${NS}><foreignObject><iframe srcdoc="&lt;img src=x onerror=${M}()&gt;"></iframe></foreignObject></svg>`,
      );
      refuteContains(out, 'srcdoc', 'the embedded-document attribute must be removed');
      refuteContains(out, M, 'the embedded payload must be gone');
    },
  },
  {
    name: 'event-handler attributes outside the common set are also removed',
    run: ({ sanitize, refuteContains }) => {
      const out = sanitize(
        `<svg ${NS}><rect onpointerdown="${M}()" onwheel="${M}()" onmouseenter="${M}()"/></svg>`,
      );
      refuteContains(out, 'onpointerdown', 'pointer event handler must be removed');
      refuteContains(out, 'onwheel', 'wheel event handler must be removed');
      refuteContains(out, 'onmouseenter', 'mouse event handler must be removed');
      refuteContains(out, M, 'no handler body may remain');
    },
  },
  {
    name: 'a resource reference that loads executable content is removed',
    run: ({ sanitize, refuteContains }) => {
      const svgData = sanitize(
        `<svg ${NS}><image href="data:image/svg+xml,&lt;svg onload=${M}()&gt;"/></svg>`,
      );
      refuteContains(svgData, 'data:image/svg+xml', 'executable data reference must be removed');
      refuteContains(svgData, M, 'the referenced payload must be gone');
      const legacy = sanitize(`<svg ${NS}><use href="vbscript:${M}()"/></svg>`);
      refuteContains(legacy, 'vbscript:', 'legacy executable scheme must not remain');
      refuteContains(legacy, M, 'the referenced payload must be gone');
    },
  },
  {
    name: 'a value that redirects an attribute to an executable target is removed',
    run: ({ sanitize, refuteContains }) => {
      const viaValues = sanitize(
        `<svg ${NS}><a href="#safe"><set attributeName="href" values="#a;javascript:${M}()"/><rect/></a></svg>`,
      );
      refuteContains(viaValues, 'javascript:', 'retargeting value must not keep an executable link');
      refuteContains(viaValues, M, 'the retarget payload must be gone');
      const viaPrefixed = sanitize(
        `<svg ${NS} xmlns:xlink="http://www.w3.org/1999/xlink"><a xlink:href="#safe"><animate attributeName="xlink:href" to="javascript:${M}()"/><rect/></a></svg>`,
      );
      refuteContains(viaPrefixed, 'javascript:', 'prefixed retarget must not keep an executable link');
      refuteContains(viaPrefixed, M, 'the retarget payload must be gone');
    },
  },
];

runSuite('security', cases, path.resolve(process.env.OUT_DIR || '.', 'results.xml'));
