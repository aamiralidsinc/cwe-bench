'use strict';

const { sanitize } = require('../support/product.js');
const { match, notMatch } = require('../support/assert.js');

const doc = (body, attrs = '') =>
  `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}>${body}</svg>`;

module.exports = {
  tests: [
    {
      name: 'executable_html_data_link_is_neutralised',
      fn() {
        const out = sanitize(
          doc(
            '<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="><text>a</text></a>',
          ),
        );
        notMatch(out, /data:text\/html/i, 'the executable data link survived');
        notMatch(out, /<a[\s>]/, 'the link element was kept around the executable URL');
        match(out, /<text[ >]/, 'the link content was removed');
      },
    },
    {
      name: 'executable_xhtml_and_svg_data_links_are_neutralised',
      fn() {
        const out = sanitize(
          doc(
            '<a href="DATA:application/xhtml+xml;charset=utf-8,%3Cscript%3Ealert(1)%3C/script%3E"><text>a</text></a>' +
              '<a href="data:image/svg+xml;base64,PHN2ZyBvbmxvYWQ9ImFsZXJ0KDEpIi8+"><text>b</text></a>' +
              '<a href="data:text/html;charset=utf-8,plain"><text>c</text></a>',
          ),
        );
        notMatch(out, /application\/xhtml\+xml/i, 'an executable XHTML document survived');
        notMatch(out, /image\/svg\+xml/i, 'an executable SVG document survived');
        notMatch(out, /text\/html/i, 'an executable HTML document survived');
        notMatch(out, /<a[\s>]/, 'an executable link element survived');
      },
    },
    {
      name: 'legacy_vbscript_link_is_neutralised',
      fn() {
        const out = sanitize(
          doc('<a href="vbscript:msgbox(1)"><text>a</text></a><a href="VBScript:msgbox(2)"><text>b</text></a>'),
        );
        notMatch(out, /vbscript:/i, 'a legacy executable link survived');
        notMatch(out, /<a[\s>]/, 'the link element was kept around the executable URL');
      },
    },
    {
      name: 'executable_scheme_with_ascii_whitespace_is_neutralised',
      fn() {
        const out = sanitize(
          doc(
            '<a href="java&#9;script:alert(1)"><text>a</text></a>' +
              '<a href="java&#10;script:alert(2)"><text>b</text></a>' +
              '<a href="java&#13;script:alert(3)"><text>c</text></a>',
          ),
        );
        notMatch(out, /alert\(1\)/, 'a tab-split executable scheme survived');
        notMatch(out, /alert\(2\)/, 'a newline-split executable scheme survived');
        notMatch(out, /alert\(3\)/, 'a carriage-return-split executable scheme survived');
        notMatch(out, /<a[\s>]/, 'the link element was kept around the executable URL');
      },
    },
    {
      name: 'namespace_prefixed_anchor_is_neutralised',
      fn() {
        const out = sanitize(
          '<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">' +
            '<svg:a href="javascript:alert(1)"><text>a</text></svg:a>' +
            '<alias:a xmlns:alias="http://www.w3.org/2000/svg" href="javascript:alert(2)"><text>b</text></alias:a>' +
            '</svg>',
        );
        notMatch(out, /alert\(1\)/, 'a prefixed anchor with an executable link survived');
        notMatch(out, /alert\(2\)/, 'a locally-declared prefixed anchor survived');
        match(out, /<text[ >]/, 'the anchor content was removed');
      },
    },
    {
      name: 'prefixed_href_with_executable_data_link_is_neutralised',
      fn() {
        const out = sanitize(
          '<svg xmlns="http://www.w3.org/2000/svg" xmlns:uwu="http://www.w3.org/1999/xlink">' +
            '<a uwu:href="data:text/html;base64,PHNjcmlwdD4="><text>a</text></a>' +
            '</svg>',
        );
        notMatch(out, /data:text\/html/i, 'an executable data link on a prefixed attribute survived');
        notMatch(out, /<a[\s>]/, 'the link element was kept around the executable URL');
        match(out, /<text[ >]/, 'the anchor content was removed');
      },
    },
  ],
};
