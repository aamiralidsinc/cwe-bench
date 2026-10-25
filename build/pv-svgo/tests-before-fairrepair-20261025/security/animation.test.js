'use strict';

const { sanitize } = require('../support/product.js');
const { match, notMatch } = require('../support/assert.js');

const doc = (body, attrs = '') =>
  `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}>${body}</svg>`;

module.exports = {
  tests: [
    {
      name: 'animation_applying_executable_url_to_link_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<a href="#t"><text>a</text><set attributeName="href" to="javascript:alert(1)"/></a><rect id="t"/>',
          ),
        );
        notMatch(out, /javascript:/i, 'an executable URL applied by animation survived');
        notMatch(out, /alert\(1\)/, 'the executable value survived');
        match(out, /<a href="#t"/, 'the ordinary link was removed');
        match(out, /<text[ >]/, 'the link content was removed');
      },
    },
    {
      name: 'animation_applying_executable_url_list_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<a href="#t"><text>a</text><animate attributeName="xlink:href" values="#one;javascript:alert(1);#two" dur="1s"/></a><rect id="t"/>',
          ),
        );
        notMatch(out, /javascript:/i, 'an executable URL inside a value list survived');
        notMatch(out, /alert\(1\)/, 'the executable value survived');
        notMatch(out, /<animate[\s>]/, 'the animating element was kept');
      },
    },
    {
      name: 'animation_applying_executable_data_url_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<a href="#t"><text>a</text><set attributeName="href" to="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="/></a><rect id="t"/>',
          ),
        );
        notMatch(out, /data:text\/html/i, 'an executable data document applied by animation survived');
        match(out, /<text[ >]/, 'the link content was removed');
      },
    },
    {
      name: 'animation_applying_executable_url_from_value_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<a href="#t"><text>a</text><animate attributeName="HREF" from="javascript:alert(1)" to="#two" dur="1s"/></a><rect id="t"/>',
          ),
        );
        notMatch(out, /javascript:/i, 'an executable URL in a start value survived');
        notMatch(out, /alert\(1\)/, 'the executable value survived');
      },
    },
  ],
};
