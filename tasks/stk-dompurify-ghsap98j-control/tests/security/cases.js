'use strict';
const assert = require('assert');

/*
 * Security cases (control task): only the advisory's own route — an application hook that removes
 * the non-root element it is called on while the library sanitizes a live tree in place. The
 * detached subtree's resource-event handlers must be gone after the call.
 */

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

  function wrapperCase(hookName, inner, attr, value) {
    add('security/hook-detach', `current node removed in ${hookName}`, () => {
      const { document, DOMPurify } = dom();
      const root = document.createElement('div');
      root.innerHTML = `<section id="wrap">${inner}</section>`;
      const node = root.querySelector(inner.match(/^<(\w+)/)[1]);
      document.body.appendChild(root);
      DOMPurify.addHook(hookName, (n) => {
        if (n.nodeType === 1 && n.id === 'wrap') n.remove();
      });
      DOMPurify.sanitize(root, { IN_PLACE: true });
      assert.strictEqual(node.getAttribute(attr), null, 'detached original is armed');
    });
  }

  wrapperCase(
    'afterSanitizeElements',
    '<img src="x" onerror="alert(1)">',
    'onerror'
  );
  wrapperCase(
    'afterSanitizeAttributes',
    '<img src="x" onerror="alert(2)">',
    'onerror'
  );
  wrapperCase(
    'afterSanitizeElements',
    '<video src="x" onerror="alert(3)"></video>',
    'onerror'
  );
  wrapperCase(
    'afterSanitizeAttributes',
    '<div onclick="alert(4)">d</div>',
    'onclick'
  );

  return out;
};
