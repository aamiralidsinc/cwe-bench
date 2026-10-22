const realDoc = global.document;
module.exports = {
  dom: {
    utils: {
      createElement: jest.fn((tag, attrs, html) => { const el = realDoc.createElement(tag); if (attrs) for (const k of Object.keys(attrs)) { if (attrs[k] != null) el.setAttribute(k, attrs[k]); } if (html) el.innerHTML = html; return el; }),
      removeItem: jest.fn((n) => n && n.parentNode && n.parentNode.removeChild(n)),
      hasClass: jest.fn((el, c) => el?.classList?.contains(c)),
    },
    check: { isIFrame: jest.fn((n) => n && n.nodeName === 'IFRAME') },
    query: { getParentElement: jest.fn(() => null), getChildNode: jest.fn(() => null), getEventTarget: jest.fn((e) => e?.target || e) },
  },
  numbers: { get: jest.fn((v, d) => { const p = parseFloat(v); return isNaN(p) ? d : p; }), is: jest.fn((v) => typeof v === 'number') },
  env: { _w: global, NO_EVENT: Symbol('NO_EVENT') },
  keyCodeMap: { key: { 13: 'Enter' }, isSpace: jest.fn((c) => c === 'Space') },
};
