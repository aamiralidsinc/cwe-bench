'use strict';

const { sanitize } = require('../support/product.js');
const { includes, match, notMatch } = require('../support/assert.js');

const doc = (body, attrs = '') =>
  `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}>${body}</svg>`;

module.exports = {
  tests: [
    {
      name: 'inert_data_links_keep_working',
      fn() {
        const out = sanitize(
          doc(
            '<a href="data:image/png;base64,iVBORw0KGgo="><text>png</text></a>' +
              '<a href="data:image/jpeg;base64,/9j/4A=="><text>jpg</text></a>' +
              '<a href="data:image/gif;base64,R0lGOD"><text>gif</text></a>',
          ),
        );
        match(out, /<a href="data:image\/png;base64,iVBORw0KGgo="/, 'the PNG data link was altered');
        match(out, /<a href="data:image\/jpeg;base64,/, 'the JPEG data link was altered');
        match(out, /<a href="data:image\/gif;base64,/, 'the GIF data link was altered');
        includes(out, 'png', 'the link content was removed');
      },
    },
    {
      name: 'embedded_visual_html_keeps_working',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject width="100" height="100">' +
              '<div class="card" style="color:red" title="card title">' +
              '<p>Hello world</p>' +
              '<img src="https://example.com/a.png" alt="a"/>' +
              '<iframe src="https://example.com/embed"></iframe>' +
              '<form action="https://example.com/post" class="f"><input name="q"/></form>' +
              '</div></foreignObject>',
          ),
        );
        includes(out, 'class="card"', 'the visual class was removed');
        includes(out, 'style="color:red"', 'the visual style was removed');
        includes(out, 'title="card title"', 'the title was removed');
        includes(out, 'src="https://example.com/a.png"', 'the ordinary image source was removed');
        // A remote frame embeds an active document: keeping or removing it are both correct, so it is not asserted.
        includes(out, 'action="https://example.com/post"', 'the ordinary form action was removed');
        includes(out, '<input', 'the form control was removed');
        includes(out, 'Hello', 'the text was removed');
        includes(out, 'world', 'the text was removed');
      },
    },
    {
      name: 'elements_from_other_vocabularies_keep_their_content',
      fn() {
        const out = sanitize(
          '<svg xmlns="http://www.w3.org/2000/svg" xmlns:custom="https://example.com/custom">' +
            '<custom:a href="javascript:alert(1)"><text>custom</text></custom:a>' +
            '<custom:foreignObject srcdoc="Custom data" title="t">Kid</custom:foreignObject>' +
            '</svg>',
        );
        match(out, /<custom:a href="javascript:alert\(1\)"/, 'a foreign-vocabulary element was altered');
        match(out, /<custom:foreignObject srcdoc="Custom data"/, 'a foreign-vocabulary element was altered');
        includes(out, 'Kid', 'the foreign-vocabulary content was removed');
      },
    },
    {
      name: 'ordinary_links_keep_working',
      fn() {
        const out = sanitize(
          doc(
            '<a href="https://example.com/x"><text>web</text></a>' +
              '<a href="#part"><text>frag</text></a>' +
              '<a href="mailto:someone@example.com"><text>mail</text></a>' +
              '<a href="relative/page.html"><text>rel</text></a>',
          ),
        );
        match(out, /<a href="https:\/\/example\.com\/x"/, 'an ordinary link was removed');
        match(out, /<a href="#part"/, 'a fragment link was removed');
        match(out, /<a href="mailto:someone@example.com"/, 'a mail link was removed');
        match(out, /<a href="relative\/page.html"/, 'a relative link was removed');
      },
    },
    {
      name: 'document_attribute_spelling_and_values_are_kept',
      fn() {
        const out = sanitize(
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" preserveAspectRatio="xMidYMid meet">' +
            '<linearGradient id="g" gradientUnits="userSpaceOnUse"><stop offset="0"/></linearGradient>' +
            '<rect width="1" height="1" aria-label="a chart"/></svg>',
        );
        includes(out, 'viewBox="0 0 10 10"', 'viewBox was changed or removed');
        includes(out, 'preserveAspectRatio="xMidYMid meet"', 'preserveAspectRatio was changed');
        includes(out, 'gradientUnits="userSpaceOnUse"', 'gradientUnits was changed');
        includes(out, 'aria-label="a chart"', 'an ordinary attribute was removed');
      },
    },
    {
      name: 'non_executable_animations_keep_working',
      fn() {
        const out = sanitize(
          doc(
            '<rect width="10" height="10"><animate attributeName="x" from="0" to="10" dur="1s"/>' +
              '<set attributeName="fill" to="red"/></rect>' +
              '<a href="#t"><text>a</text><animate attributeName="href" values="#one;#two" dur="1s"/></a>',
          ),
        );
        match(out, /<animate attributeName="x" from="0" to="10"/, 'a harmless animation was removed');
        match(out, /<set attributeName="fill" to="red"/, 'a harmless animation was removed');
        match(out, /<animate attributeName="href" values="#one;#two"/, 'a harmless animation was removed');
        notMatch(out, /javascript:/i, 'an executable URL was introduced');
      },
    },
    {
      name: 'foreign_object_inert_attributes_are_kept',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject width="50" height="50"><div data-kind="note" class="k">t</div></foreignObject>',
          ),
        );
        includes(out, 'width="50"', 'an ordinary attribute was removed');
        includes(out, 'data-kind="note"', 'an ordinary author attribute was removed');
        includes(out, 'class="k"', 'a class was removed');
      },
    },
  ],
};
