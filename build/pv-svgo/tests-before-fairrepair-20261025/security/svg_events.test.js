'use strict';

const { sanitize } = require('../support/product.js');
const { match, notMatch } = require('../support/assert.js');

const doc = (body, attrs = '') =>
  `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}>${body}</svg>`;

module.exports = {
  tests: [
    {
      name: 'pointer_event_handler_on_svg_root_is_removed',
      fn() {
        const out = sanitize(
          doc('<rect width="1" height="1"/>', 'onpointerdown="alert(1)"'),
        );
        notMatch(out, /onpointerdown/i, 'a pointer event handler survived');
        match(out, /<rect[ >/]/, 'the element was removed');
      },
    },
    {
      name: 'wheel_and_auxclick_handlers_are_removed',
      fn() {
        const out = sanitize(
          doc('<rect width="1" height="1" onwheel="alert(1)" onauxclick="alert(2)"/>'),
        );
        notMatch(out, /onwheel/i, 'a wheel handler survived');
        notMatch(out, /onauxclick/i, 'an auxiliary-click handler survived');
        match(out, /<rect[ >/]/, 'the element was removed');
      },
    },
    {
      name: 'html_only_event_handler_is_removed',
      fn() {
        const out = sanitize(
          doc('<circle r="1" onanimationstart="alert(1)" onbeforetoggle="alert(2)"/>'),
        );
        notMatch(out, /onanimationstart/i, 'an animation event handler survived');
        notMatch(out, /onbeforetoggle/i, 'a toggle event handler survived');
      },
    },
    {
      name: 'mixed_case_event_handler_is_removed',
      fn() {
        const out = sanitize(
          doc('<rect width="1" height="1" onClick="alert(1)"/>', 'onLoad="alert(2)"'),
        );
        notMatch(out, /onclick/i, 'a mixed-case click handler survived');
        notMatch(out, /onload/i, 'a mixed-case load handler survived');
      },
    },
    {
      name: 'mixed_case_event_handler_on_nested_element_is_removed',
      fn() {
        const out = sanitize(
          doc('<g><rect width="1" height="1" ONMOUSEOVER="alert(1)"/></g>'),
        );
        notMatch(out, /onmouseover/i, 'a nested mixed-case handler survived');
        match(out, /<g[ >]/, 'the container was removed');
      },
    },
  ],
};
