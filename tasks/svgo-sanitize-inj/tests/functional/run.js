'use strict';
// Functional suite: legitimate documents must pass through the sanitation pass
// unchanged (beyond the removal the pass has always done). These guard against
// an over-broad fix that strips benign content. Each case passes on the
// vulnerable tree and must keep passing on a correct fix.
const path = require('path');
const { runSuite } = require('../support/runner.js');

const NS = 'xmlns="http://www.w3.org/2000/svg"';

const cases = [
  {
    name: 'ordinary markup survives while an executable element is removed',
    run: ({ sanitize, refuteContains, assertContains }) => {
      const out = sanitize(`<svg ${NS}><script>blocked()</script><rect id="keep" fill="red"/></svg>`);
      refuteContains(out, '<script', 'the executable element should still be removed');
      assertContains(out, 'id="keep"', 'a sibling element must be preserved');
    },
  },
  {
    name: 'an inert inline data reference is preserved',
    run: ({ sanitize, assertContains }) => {
      const out = sanitize(`<svg ${NS}><image href="data:image/png;base64,AAAABBBBCCCC"/></svg>`);
      assertContains(out, 'data:image/png;base64,AAAABBBBCCCC', 'inert data image must be kept');
    },
  },
  {
    name: 'benign embedded HTML content is preserved',
    run: ({ sanitize, assertContains }) => {
      const out = sanitize(
        `<svg ${NS}><foreignObject><div class="c" style="color:red" title="t">hello<img src="logo.png"/></div></foreignObject></svg>`,
      );
      assertContains(out, 'class="c"', 'class must be kept');
      assertContains(out, 'title="t"', 'title must be kept');
      assertContains(out, 'src="logo.png"', 'a non-executable resource reference must be kept');
    },
  },
  {
    name: 'an ordinary navigable link is preserved',
    run: ({ sanitize, assertContains }) => {
      const out = sanitize(`<svg ${NS}><a href="https://example.com/page"><rect/></a></svg>`);
      assertContains(out, 'https://example.com/page', 'a safe link must be preserved');
    },
  },
  {
    name: 'elements in a namespace that is not executable are preserved',
    run: ({ sanitize, assertContains }) => {
      const out = sanitize(
        `<svg ${NS} xmlns:zz="http://teaparty.diy"><zz:script>not executable</zz:script></svg>`,
      );
      assertContains(out, 'zz:script', 'a non-executable custom-namespace element must be kept');
    },
  },
  {
    name: 'a benign animation is preserved',
    run: ({ sanitize, assertContains }) => {
      const out = sanitize(`<svg ${NS}><rect><set attributeName="opacity" to="0"/></rect></svg>`);
      assertContains(out, 'attributeName="opacity"', 'a benign animation must be kept');
      assertContains(out, 'to="0"', 'the animation target value must be kept');
    },
  },
];

runSuite('functional', cases, path.resolve(process.env.OUT_DIR || '.', 'results.xml'));
