'use strict';
const assert = require('assert');

module.exports = function (createDOMPurify, JSDOM) {
  function dom() {
    const { window } = new JSDOM('<!DOCTYPE html><body></body>', {
      runScripts: 'dangerously',
    });
    const DOMPurify = createDOMPurify(window);
    return { window, document: window.document, DOMPurify };
  }
  const out = [];
  const add = (classname, name, run) => out.push({ classname, name, run });

  // ---- documented node-removing hooks keep working (string path) ----
  add('functional/hooks', 'beforeSanitizeAttributes removes empty elements', () => {
    const { DOMPurify } = dom();
    DOMPurify.addHook('beforeSanitizeAttributes', (node) => {
      if (node.nodeType === 1 && !node.hasChildNodes() && !node.textContent) {
        node.remove();
      }
    });
    const clean = DOMPurify.sanitize('<p>Not empty</p><p class="empty"></p>');
    assert.ok(/Not empty/.test(clean), clean);
    assert.ok(!/class="empty"/.test(clean), clean);
  });

  add('functional/hooks', 'uponSanitizeElement removes an allowed footer', () => {
    const { DOMPurify } = dom();
    DOMPurify.setConfig({ ALLOWED_TAGS: ['div', '#text', 'footer'] });
    DOMPurify.addHook('uponSanitizeElement', (node) => {
      if (node.nodeType === 1 && node.tagName === 'FOOTER') node.remove();
    });
    const clean = DOMPurify.sanitize(
      '<div>This should remain</div><footer>gone</footer>'
    );
    assert.ok(/This should remain/.test(clean), clean);
    assert.ok(!/footer|gone/.test(clean), clean);
  });

  // ---- attributes a hook adds to surviving nodes are kept ----
  add('functional/hook-attrs', 'hook-added attribute survives in place', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML = '<b>keep</b>';
    const b = root.querySelector('b');
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.nodeType === 1 && node.tagName === 'B') {
        node.setAttribute('data-keep', '1');
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(b.getAttribute('data-keep'), '1');
    assert.ok(/<b data-keep="1">/.test(root.innerHTML), root.innerHTML);
  });

  add('functional/hook-attrs', 'hook-added attribute survives in template content', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML = '<template><b>keep</b></template>';
    const b = root.querySelector('template').content.querySelector('b');
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.nodeType === 1 && node.tagName === 'B') {
        node.setAttribute('data-keep', '1');
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(b.getAttribute('data-keep'), '1');
  });

  add('functional/hook-attrs', 'hook-added attribute survives in a shadow root', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML = '<div id="host"></div>';
    const sr = root.querySelector('#host').attachShadow({ mode: 'open' });
    sr.innerHTML = '<b>keep</b>';
    const b = sr.querySelector('b');
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.nodeType === 1 && node.tagName === 'B') {
        node.setAttribute('data-keep', '1');
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(b.getAttribute('data-keep'), '1');
  });

  // ---- public removal inventory still records removals ----
  add('functional/inventory', 'removed entries stay readable after sanitize', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML = '<p>a</p><x-not-allowed>b</x-not-allowed>';
    document.body.appendChild(root);
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.ok(Array.isArray(DOMPurify.removed), 'removed is an array');
    assert.ok(
      DOMPurify.removed.some((entry) => entry && entry.element),
      'the removed element is recorded'
    );
    assert.ok(/b/.test(root.innerHTML), 'kept content is preserved');
  });

  // ---- documented refusal contract for refused roots ----
  add('functional/refusal', 'forbidden in-place root still throws', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('script');
    document.body.appendChild(root);
    assert.throws(
      () => DOMPurify.sanitize(root, { IN_PLACE: true }),
      'a forbidden root must be refused'
    );
  });

  add('functional/refusal', 'clobbered in-place root is refused or stripped', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('form');
    root.innerHTML =
      '<input name="nodeName" onmouseover="alert(1)">' +
      '<input name="attributes" onfocus="alert(2)">';
    document.body.appendChild(root);
    if (typeof root.nodeName !== 'string') {
      assert.throws(
        () => DOMPurify.sanitize(root, { IN_PLACE: true }),
        'a clobbered root must be refused'
      );
    } else {
      const clean = DOMPurify.sanitize(root, { IN_PLACE: true });
      const html = clean.outerHTML || '';
      assert.ok(!/on\w+\s*=/i.test(html), 'no handler survived: ' + html);
    }
  });

  // ---- ordinary sanitization is unchanged ----
  add('functional/normal', 'in-place sanitize keeps allowed content and returns the node', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML =
      '<b>ok</b><img src="x" onerror="alert(1)">' +
      '<a href="javascript:alert(2)">l</a>';
    document.body.appendChild(root);
    const ret = DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(ret, root);
    assert.strictEqual(root.querySelector('img').getAttribute('onerror'), null);
    assert.strictEqual(root.querySelector('a').getAttribute('href'), null);
    assert.ok(/<b>ok<\/b>/.test(root.innerHTML), root.innerHTML);
  });

  add('functional/normal', 'string sanitize is unchanged', () => {
    const { DOMPurify } = dom();
    assert.strictEqual(
      DOMPurify.sanitize('<b>ok</b><img src="x" onerror="alert(1)">'),
      '<b>ok</b><img src="x">'
    );
  });

  add('functional/normal', 'normal elements still run the element hook', () => {
    const { DOMPurify } = dom();
    let seen = 0;
    DOMPurify.addHook('afterSanitizeElements', (node) => {
      if (node.nodeType === 1 && node.tagName === 'B') seen += 1;
    });
    DOMPurify.sanitize('<b>ok</b><i>i</i>');
    assert.strictEqual(seen, 1);
  });

  // ---- configured custom elements still survive ----
  add('functional/custom-elements', 'configured custom element survives', () => {
    const { DOMPurify } = dom();
    const clean = DOMPurify.sanitize('<x-foo data-x="1">hi</x-foo>', {
      CUSTOM_ELEMENT_HANDLING: {
        tagNameCheck: /^x-/,
        attributeNameCheck: /^data-/,
        allowCustomizedBuiltInElements: false,
      },
    });
    assert.ok(/<x-foo data-x="1">hi<\/x-foo>/.test(clean), clean);
  });

  // ---- coupled values next to the hidden routes ----
  add('functional/coupled', 'a node-removing hook still removes a subtree in place', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML =
      '<div id="outer"><b>gone</b></div><p id="stay">stay</p>';
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeElements', (node) => {
      if (node.id === 'stay') {
        const outer = root.querySelector('#outer');
        if (outer && outer.parentNode) outer.remove();
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(root.querySelector('#outer'), null, 'outer is removed');
    assert.ok(/stay/.test(root.innerHTML), root.innerHTML);
  });

  add('functional/coupled', 'a re-entrant sanitize still returns its own result', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML = '<b>outer</b><section id="trigger">t</section>';
    document.body.appendChild(root);
    let inner = null;
    DOMPurify.addHook('afterSanitizeElements', (node) => {
      if (node.id === 'trigger') {
        inner = DOMPurify.sanitize('<i>inner</i>');
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true, KEEP_CONTENT: false });
    assert.strictEqual(inner, '<i>inner</i>');
    assert.ok(/<b>outer<\/b>/.test(root.innerHTML), root.innerHTML);
  });

  return out;
};
