'use strict';

const { sanitize } = require('../support/product.js');
const { match, notMatch } = require('../support/assert.js');

const doc = (body, attrs = '') =>
  `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}>${body}</svg>`;

module.exports = {
  tests: [
    {
      name: 'nested_event_handler_in_embedded_html_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject width="10" height="10"><div><p onbeforetoggle="alert(1)">x</p></div></foreignObject>',
          ),
        );
        notMatch(out, /onbeforetoggle/i, 'a handler on embedded HTML survived');
        match(out, /<p[ >]/, 'the visual paragraph was removed');
      },
    },
    {
      name: 'deeply_nested_event_handler_in_embedded_html_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject><div><section><span onclick="alert(1)">x</span></section></div></foreignObject>',
          ),
        );
        notMatch(out, /onclick/i, 'a deeply nested handler survived');
        match(out, /<span[ >]/, 'the visual span was removed');
      },
    },
    {
      name: 'srcdoc_on_direct_child_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject><iframe srcdoc="&lt;script&gt;alert(1)&lt;/script&gt;"></iframe></foreignObject>',
          ),
        );
        notMatch(out, /srcdoc/i, 'an embedded document survived');
        // The frame may be kept (inert) or removed: the instruction allows either.
      },
    },
    {
      name: 'srcdoc_on_nested_child_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject><div><iframe srcdoc="&lt;script&gt;alert(1)&lt;/script&gt;" src="https://example.com/x"></iframe></div></foreignObject>',
          ),
        );
        notMatch(out, /srcdoc/i, 'a nested embedded document survived');
        // The frame (and so its ordinary src) may be kept or removed: the instruction allows either.
      },
    },
    {
      name: 'executable_url_attributes_in_embedded_html_are_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject>' +
              '<form action="javascript:alert(1)"><button formaction="vbscript:msgbox(1)">b</button></form>' +
              '<object data="data:text/html,&lt;script&gt;alert(1)&lt;/script&gt;"></object>' +
              '<iframe src="data:image/svg+xml;base64,PHN2Zy8+"></iframe>' +
              '</foreignObject>',
          ),
        );
        notMatch(out, /javascript:/i, 'an executable link survived');
        notMatch(out, /vbscript:/i, 'a legacy executable link survived');
        notMatch(out, /data:text\/html/i, 'an executable data document survived');
        notMatch(out, /data:image\/svg\+xml/i, 'an executable SVG document survived');
        match(out, /<form[ >/]/, 'the visual form was removed');
        match(out, /<button[ >/]/, 'the visual button was removed');
        // <object> and <iframe> are active-document containers: kept inert or removed, either is correct.
      },
    },
    {
      name: 'prefixed_foreign_object_content_is_sanitised',
      fn() {
        const out = sanitize(
          '<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" ' +
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">' +
            '<svg:foreignObject><xhtml:iframe srcdoc="x"/><xhtml:div onpointerdown="a()">t</xhtml:div></svg:foreignObject>' +
            '<alias:foreignObject xmlns:alias="http://www.w3.org/2000/svg"><xhtml:div onpointerdown="b()">u</xhtml:div></alias:foreignObject>' +
            '</svg>',
        );
        notMatch(out, /srcdoc/i, 'an embedded document in a prefixed element survived');
        notMatch(out, /onpointerdown/i, 'a handler in a prefixed element survived');
        match(out, /<xhtml:div[ >]/, 'visual content in a prefixed element was removed');
      },
    },
    {
      name: 'event_handler_on_foreign_object_element_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject onbeforetoggle="alert(1)" width="10" height="10"><div>t</div></foreignObject>',
          ),
        );
        notMatch(out, /onbeforetoggle/i, 'a handler on the embedded-document element survived');
        match(out, /<div[ >]/, 'the visual content was removed');
      },
    },
    {
      name: 'script_elements_in_embedded_html_are_removed',
      fn() {
        const out = sanitize(
          '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xhtml="http://www.w3.org/1999/xhtml">' +
            '<foreignObject><script>alert(11)</script><xhtml:script>alert(22)</xhtml:script><p>t</p></foreignObject>' +
            '</svg>',
        );
        notMatch(out, /alert\(11\)/, 'a script element survived');
        notMatch(out, /alert\(22\)/, 'a prefixed script element survived');
        match(out, /<p[ >]/, 'the visual paragraph was removed');
      },
    },
    {
      name: 'mixed_case_script_element_is_removed',
      fn() {
        const out = sanitize(
          doc('<foreignObject><SCRIPT>alert(1)</SCRIPT><p>t</p></foreignObject>'),
        );
        notMatch(out, /alert\(1\)/, 'a script element with different case survived');
        match(out, /<p[ >]/, 'the visual paragraph was removed');
      },
    },
    {
      name: 'executable_data_document_in_embedded_html_is_removed',
      fn() {
        const out = sanitize(
          doc(
            '<foreignObject>' +
              '<iframe src="DATA:TEXT/HTML;charset=utf-8,%3Cscript%3Ealert(1)%3C/script%3E"></iframe>' +
              '<embed src="data:application/xhtml+xml;base64,PHNjcmlwdC8+"/>' +
              '</foreignObject>',
          ),
        );
        notMatch(out, /data:/i, 'an executable data document survived');
        // The frame may be kept (inert) or removed.
      },
    },
  ],
};
