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
  const armed = (img) => img.getAttribute('onerror');

  // ---- concept: hook-detached subtree (current node, every hook site) ----
  for (const hookName of [
    'beforeSanitizeElements',
    'uponSanitizeElement',
    'afterSanitizeElements',
    'beforeSanitizeAttributes',
    'afterSanitizeAttributes',
  ]) {
    add('security/hook-detach', `current node removed in ${hookName}`, () => {
      const { document, DOMPurify } = dom();
      const root = document.createElement('div');
      root.innerHTML =
        '<section id="wrap"><img src="x" onerror="alert(1)"></section>';
      const img = root.querySelector('img');
      document.body.appendChild(root);
      DOMPurify.addHook(hookName, (node) => {
        if (node.nodeType === 1 && node.id === 'wrap') node.remove();
      });
      DOMPurify.sanitize(root, { IN_PLACE: true });
      assert.strictEqual(
        armed(img),
        null,
        `${hookName}: the detached original keeps a live handler`
      );
    });
  }

  // ---- concept: a hook detaches an ancestor of the node it was called on ----
  add('security/hook-detach', 'ancestor removed in an element hook', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML =
      '<div id="outer"><span id="inner">t</span>' +
      '<img src="x" onerror="alert(2)"></div>';
    const img = root.querySelector('img');
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeElements', (node) => {
      if (node.id === 'inner') {
        const outer = root.querySelector('#outer');
        if (outer && outer.parentNode) outer.remove();
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(armed(img), null, 'ancestor removal leaves it armed');
  });

  add('security/hook-detach', 'ancestor removed in an attribute hook', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML =
      '<div id="outer"><span id="inner">t</span>' +
      '<img src="x" onerror="alert(3)"></div>';
    const img = root.querySelector('img');
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.id === 'inner') {
        const outer = root.querySelector('#outer');
        if (outer && outer.parentNode) outer.remove();
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(armed(img), null, 'ancestor removal leaves it armed');
  });

  // ---- concept: hook removal inside an attached shadow root ----
  add('security/hook-detach', 'removal inside an attached shadow root', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML = '<div id="host"></div>';
    const host = root.querySelector('#host');
    const sr = host.attachShadow({ mode: 'open' });
    sr.innerHTML =
      '<section id="sw"><img src="x" onerror="alert(5)"></section>';
    const img = sr.querySelector('img');
    document.body.appendChild(root);
    DOMPurify.addHook('afterSanitizeElements', (node) => {
      if (node.id === 'sw') node.remove();
    });
    DOMPurify.sanitize(root, { IN_PLACE: true });
    assert.strictEqual(armed(img), null, 'detached shadow content is armed');
  });

  // ---- concept: abort teardown must neutralize before detaching ----
  add('security/abort-teardown', 'aborted walk leaves no armed original', () => {
    const { window, document, DOMPurify } = dom();
    assert.ok(window.customElements, 'custom elements are unavailable');
    if (!window.customElements.get('x-surgeon-gate')) {
      class XSurgeon extends window.HTMLElement {
        disconnectedCallback() {
          const w = root.querySelector('#abort-wrap');
          if (w && w.parentNode) w.remove();
        }
      }
      window.customElements.define('x-surgeon-gate', XSurgeon);
    }
    const root = document.createElement('div');
    root.innerHTML =
      '<x-abort-wrap id="abort-wrap"><x-surgeon-gate></x-surgeon-gate>' +
      '</x-abort-wrap>' +
      '<img id="abort-img" src="x" onerror="alert(6)">' +
      '<div id="abort-div" onclick="alert(7)">d</div>';
    const img = root.querySelector('#abort-img');
    const div = root.querySelector('#abort-div');
    document.body.appendChild(root);
    try {
      DOMPurify.sanitize(root, { IN_PLACE: true });
    } catch (_) {
      /* A thrown abort is an accepted contract; the tree must still be inert. */
    }
    assert.strictEqual(img.getAttribute('onerror'), null, 'onerror survives');
    assert.strictEqual(div.getAttribute('onclick'), null, 'onclick survives');
  });

  // ---- concept: removals neutralized at detach time (re-entrant call) ----
  add('security/removal-inventory', 're-entrant sanitize from an element hook', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML =
      '<x-wrap><img src="x" onerror="alert(8)"></x-wrap>' +
      '<section id="trigger">t</section>';
    const img = root.querySelector('img');
    document.body.appendChild(root);
    let done = false;
    DOMPurify.addHook('afterSanitizeElements', (node) => {
      if (node.id === 'trigger' && !done) {
        done = true;
        DOMPurify.sanitize('<b>inner</b>');
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true, KEEP_CONTENT: false });
    assert.ok(done, 'precondition: the nested call ran');
    assert.strictEqual(armed(img), null, 'earlier removal stays armed');
  });

  add('security/removal-inventory', 're-entrant sanitize from a second element hook', () => {
    const { document, DOMPurify } = dom();
    const root = document.createElement('div');
    root.innerHTML =
      '<x-wrap><img src="x" onerror="alert(9)"></x-wrap>' +
      '<section id="trigger">t</section>';
    const img = root.querySelector('img');
    document.body.appendChild(root);
    let done = false;
    DOMPurify.addHook('beforeSanitizeElements', (node) => {
      if (node.id === 'trigger' && !done) {
        done = true;
        DOMPurify.sanitize('<b>inner</b>');
      }
    });
    DOMPurify.sanitize(root, { IN_PLACE: true, KEEP_CONTENT: false });
    assert.ok(done, 'precondition: the nested call ran');
    assert.strictEqual(armed(img), null, 'earlier removal stays armed');
  });

  return out;
};
