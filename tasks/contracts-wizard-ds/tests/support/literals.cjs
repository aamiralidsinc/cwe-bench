'use strict';
// Test-side reader for generated source. It decides two things without using any product code:
//   1. whether a plain marker token appears outside every string literal and comment, and
//   2. whether a Solidity/JavaScript string literal at a known place is well formed and decodes
//      to the expected text.
// The grammar implemented here is the one the generated files target: Solidity double-quoted
// literals (printable ASCII only, with the escape set solc accepts) and unicode"..." literals
// (raw text except quote, backslash, CR, LF and VT), plus ordinary JavaScript string literals.

const ROOT = process.env.PRODUCT_ROOT || '/workspace';
const SRC = `${ROOT}/packages/core/solidity/src/`;

function src(name) {
  return require(SRC + name);
}

function isWs(c) {
  return c === ' ' || c === '\t' || c === '\n' || c === '\r';
}

// ---------------------------------------------------------------------------------------------
// Lexical walk. Returns the offsets of `marker` that start in code (not in a literal/comment).
// lang: 'sol' | 'js'. Template literals are only recognised in 'js'.
// ---------------------------------------------------------------------------------------------
function uncontainedOccurrences(text, marker, lang) {
  const found = [];
  const n = text.length;
  let i = 0;
  let state = 'normal'; // normal | line | block | str | tmpl
  let quote = null;
  let exprDepth = 0; // >0 while inside ${ ... } of a template literal
  let inTemplateExpr = false;

  while (i < n) {
    const c = text[i];

    if (state === 'normal') {
      if (c === '{' && inTemplateExpr) exprDepth += 1;
      if (c === '}' && inTemplateExpr) {
        exprDepth -= 1;
        if (exprDepth === 0) {
          inTemplateExpr = false;
          state = 'tmpl';
          i += 1;
          continue;
        }
      }
      if (text.startsWith(marker, i)) found.push(i);
      if (c === '/' && text[i + 1] === '/') {
        state = 'line';
        i += 2;
        continue;
      }
      if (c === '/' && text[i + 1] === '*') {
        state = 'block';
        i += 2;
        continue;
      }
      if (c === '"' || c === "'") {
        state = 'str';
        quote = c;
        i += 1;
        continue;
      }
      if (lang === 'js' && c === '`') {
        state = 'tmpl';
        i += 1;
        continue;
      }
      i += 1;
      continue;
    }

    if (state === 'line') {
      if (c === '\n' || c === '\r') state = 'normal';
      i += 1;
      continue;
    }

    if (state === 'block') {
      if (c === '*' && text[i + 1] === '/') {
        state = 'normal';
        i += 2;
        continue;
      }
      i += 1;
      continue;
    }

    if (state === 'str') {
      if (c === '\\') {
        i += 2;
        continue;
      }
      if (c === '\n' || c === '\r' || (lang === 'sol' && c === '\x0b')) {
        // A raw line terminator inside a quoted literal is not part of the literal.
        state = 'normal';
        i += 1;
        continue;
      }
      if (c === quote) {
        state = 'normal';
        i += 1;
        continue;
      }
      i += 1;
      continue;
    }

    if (state === 'tmpl') {
      if (c === '\\') {
        i += 2;
        continue;
      }
      if (c === '`') {
        state = 'normal';
        i += 1;
        continue;
      }
      if (c === '$' && text[i + 1] === '{') {
        state = 'normal';
        inTemplateExpr = true;
        exprDepth = 1;
        i += 2;
        continue;
      }
      i += 1;
      continue;
    }
  }

  return found.map(offset => {
    const line = text.slice(0, offset).split(/\r?\n/).length;
    return { offset, line, text: text.split(/\r?\n/)[line - 1] || '' };
  });
}

// Every occurrence of the marker must be inside a literal or comment.
function assertMarkerContained(assert, text, marker, lang, where) {
  const hits = uncontainedOccurrences(text, marker, lang);
  assert.equal(
    hits.length,
    0,
    `${where}: the supplied value introduced source outside a literal or comment: ` +
      hits.map(h => `line ${h.line}: ${h.text.trim().slice(0, 120)}`).join(' | '),
  );
}

// ---------------------------------------------------------------------------------------------
// Literal parsing.
// parseLiteral(text, index, lang) -> { value, end, kind } | null
// ---------------------------------------------------------------------------------------------
const HEX = /^[0-9a-fA-F]$/;

function decodeEscape(text, i, lang, kind) {
  // text[i] is the backslash
  const c = text[i + 1];
  if (c === '\\') return { value: '\\', next: i + 2 };
  if (c === '"') return { value: '"', next: i + 2 };
  if (c === "'") return { value: "'", next: i + 2 };
  if (c === 'n') return { value: '\n', next: i + 2 };
  if (c === 'r') return { value: '\r', next: i + 2 };
  if (c === 't') return { value: '\t', next: i + 2 };
  if (c === 'b' && (lang === 'js' || kind === 'js')) return { value: '\b', next: i + 2 };
  if (c === 'f' && (lang === 'js' || kind === 'js')) return { value: '\f', next: i + 2 };
  if (c === 'v' && (lang === 'js' || kind === 'js')) return { value: '\v', next: i + 2 };
  if (c === '0' && (lang === 'js' || kind === 'js')) return { value: '\0', next: i + 2 };
  if (c === '\n') return { value: '', next: i + 2 }; // line continuation
  if (c === 'x') {
    const h = text.slice(i + 2, i + 4);
    if (h.length === 2 && HEX.test(h[0]) && HEX.test(h[1])) {
      return { value: String.fromCharCode(parseInt(h, 16)), next: i + 4 };
    }
    return null;
  }
  if (c === 'u') {
    if (text[i + 2] === '{' && (lang === 'js' || kind === 'js')) {
      const close = text.indexOf('}', i + 3);
      const h = close > i + 3 ? text.slice(i + 3, close) : '';
      if (close > i + 3 && /^[0-9a-fA-F]{1,6}$/.test(h)) {
        return { value: String.fromCodePoint(parseInt(h, 16)), next: close + 1 };
      }
      return null;
    }
    const h = text.slice(i + 2, i + 6);
    if (h.length === 4 && [...h].every(ch => HEX.test(ch))) {
      return { value: String.fromCharCode(parseInt(h, 16)), next: i + 6 };
    }
    return null;
  }
  return null; // not an escape any target language accepts
}

function parseLiteral(text, index, lang) {
  let i = index;
  let kind;
  let closing;

  if (lang === 'sol' && text.startsWith('unicode"', i)) {
    kind = 'sol-unicode';
    i += 8;
    closing = '"';
  } else if (text[i] === '"') {
    kind = lang === 'sol' ? 'sol-plain' : 'js';
    i += 1;
    closing = '"';
  } else if (lang === 'js' && text[i] === "'") {
    kind = 'js';
    i += 1;
    closing = "'";
  } else {
    return null;
  }

  let value = '';
  while (i < text.length) {
    const c = text[i];
    if (c === '\\') {
      const esc = decodeEscape(text, i, kind === 'js' ? 'js' : 'sol', kind);
      if (esc === null) return null;
      value += esc.value;
      i = esc.next;
      continue;
    }
    if (c === closing) {
      return { value, end: i + 1, kind };
    }
    if (c === '\n' || c === '\r' || (kind === 'sol-unicode' && c === '\x0b')) {
      return null; // raw line terminator cannot appear in the literal
    }
    if (kind === 'sol-plain') {
      // Printable ASCII only, minus quote and backslash (handled above).
      const code = c.codePointAt(0);
      if (code < 0x20 || code > 0x7e) return null;
      value += c;
      i += 1;
      continue;
    }
    value += c;
    i += 1;
  }
  return null; // unterminated
}

// Find `marker`, then parse a literal that starts after it (whitespace allowed between).
function literalAfter(text, marker, lang, from = 0) {
  const at = text.indexOf(marker, from);
  if (at < 0) return { at: -1, literal: null, why: `marker not found: ${marker}` };
  let i = at + marker.length;
  while (i < text.length && isWs(text[i])) i += 1;
  return { at: i, literal: parseLiteral(text, i, lang), why: `no literal after ${marker}` };
}

// Find startMarker, then the first marker after it, then parse the literal after that marker.
function literalAfterBoth(text, startMarker, marker, lang) {
  const start = text.indexOf(startMarker);
  if (start < 0) return { at: -1, literal: null, why: `start marker not found: ${startMarker}` };
  return literalAfter(text, marker, lang, start + startMarker.length);
}

function jsLiteralAfter(text, marker, from = 0) {
  return literalAfter(text, marker, 'js', from);
}

function solLiteralAfter(text, marker, from = 0) {
  return literalAfter(text, marker, 'sol', from);
}

function zipText(zip, key) {
  const f = zip.file(key);
  if (f === null || f === undefined) throw new Error(`generated file missing: ${key}`);
  return f.async('string');
}

// The generated file name contains the contract identifier derived from the option, so tests
// locate it by pattern instead of recomputing that identifier.
function zipKeyByRegex(zip, re) {
  const key = Object.keys(zip.files).find(k => re.test(k) && !zip.files[k].dir);
  if (key === undefined) throw new Error(`no generated file matching ${re}`);
  return key;
}

module.exports = {
  ROOT,
  SRC,
  src,
  uncontainedOccurrences,
  assertMarkerContained,
  parseLiteral,
  literalAfter,
  literalAfterBoth,
  jsLiteralAfter,
  solLiteralAfter,
  zipText,
  zipKeyByRegex,
};
