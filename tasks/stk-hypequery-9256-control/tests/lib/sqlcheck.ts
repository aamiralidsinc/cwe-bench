/**
 * A small reader for the SQL that the product generates.
 *
 * It tokenizes a statement with ClickHouse string-literal rules (a backslash
 * escapes the next character, a doubled quote is a quote, quotes are doubled or
 * backslash-escaped), then exposes two views the tests use:
 *
 *  - stringLiterals(sql): the decoded text of every string literal, so a test
 *    can ask whether a supplied value is carried as one literal;
 *  - normalizedShape(sql): the statement's token skeleton with literals,
 *    numbers and identifiers replaced by placeholders and comments kept, so a
 *    test can ask whether a supplied input changed the statement's structure.
 *
 * Neither depends on how the product escapes anything; any escaping that keeps
 * the value inside one literal yields the same shape.
 */

export type TokenKind = 'word' | 'ident' | 'string' | 'number' | 'punct' | 'comment';

export interface Token {
  kind: TokenKind;
  text: string;
  value?: string;
  /** Offset of the first character in the source text. */
  start: number;
  /** Offset one past the last character in the source text. */
  end: number;
}

const KEYWORDS = new Set([
  'SELECT', 'FROM', 'WHERE', 'PREWHERE', 'GROUP', 'BY', 'WITH', 'TOTALS', 'HAVING',
  'ORDER', 'LIMIT', 'OFFSET', 'UNION', 'ALL', 'DISTINCT', 'AS', 'JOIN', 'LEFT', 'RIGHT',
  'INNER', 'OUTER', 'FULL', 'CROSS', 'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
  'IS', 'NULL', 'TRUE', 'FALSE', 'ARRAY', 'ASC', 'DESC', 'CASE', 'WHEN', 'THEN', 'ELSE',
  'END', 'INTERVAL', 'FINAL', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'DELETE', 'SET',
  'DROP', 'TABLE', 'CREATE', 'ALTER', 'GRANT', 'REVOKE', 'SYSTEM', 'FORMAT', 'GLOBAL',
  'NOT', 'EXISTS', 'CAST',
]);

function isWordStart(ch: string): boolean {
  return /[A-Za-z_$]/.test(ch);
}

function isWordChar(ch: string): boolean {
  return /[A-Za-z0-9_$]/.test(ch);
}

function isDigit(ch: string): boolean {
  return ch >= '0' && ch <= '9';
}

export function tokenize(sql: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;

  while (i < sql.length) {
    const ch = sql[i]!;

    if (/\s/.test(ch)) {
      i += 1;
      continue;
    }

    // Line comments.
    if ((ch === '-' && sql[i + 1] === '-') || (ch === '/' && sql[i + 1] === '/') ||
        (ch === '#' && (sql[i + 1] === undefined || /\s/.test(sql[i + 1]!)))) {
      const start = i;
      while (i < sql.length && sql[i] !== '\n') i += 1;
      tokens.push({ kind: 'comment', text: sql.slice(start, i), start, end: i });
      continue;
    }

    // Block comment (nested, as ClickHouse allows).
    if (ch === '/' && sql[i + 1] === '*') {
      const start = i;
      let depth = 0;
      while (i < sql.length) {
        if (sql[i] === '/' && sql[i + 1] === '*') { depth += 1; i += 2; continue; }
        if (sql[i] === '*' && sql[i + 1] === '/') {
          depth -= 1;
          i += 2;
          if (depth === 0) break;
          continue;
        }
        i += 1;
      }
      tokens.push({ kind: 'comment', text: sql.slice(start, i), start, end: i });
      continue;
    }

    // String literal: backslash escapes the next character, '' is a quote.
    if (ch === "'") {
      const start = i;
      i += 1;
      let value = '';
      while (i < sql.length) {
        const c = sql[i]!;
        if (c === '\\') {
          if (i + 1 < sql.length) value += sql[i + 1];
          i += 2;
          continue;
        }
        if (c === "'") {
          if (sql[i + 1] === "'") { value += "'"; i += 2; continue; }
          i += 1;
          break;
        }
        value += c;
        i += 1;
      }
      tokens.push({ kind: 'string', text: sql.slice(start, i), value, start, end: i });
      continue;
    }

    // Quoted identifier.
    if (ch === '"' || ch === '`') {
      const quote = ch;
      const start = i;
      i += 1;
      let value = '';
      while (i < sql.length) {
        const c = sql[i]!;
        if (c === '\\') {
          if (i + 1 < sql.length) value += sql[i + 1];
          i += 2;
          continue;
        }
        if (c === quote) {
          if (sql[i + 1] === quote) { value += quote; i += 2; continue; }
          i += 1;
          break;
        }
        value += c;
        i += 1;
      }
      tokens.push({ kind: 'ident', text: sql.slice(start, i), value, start, end: i });
      continue;
    }

    // Number.
    if (isDigit(ch) || (ch === '.' && isDigit(sql[i + 1] ?? ''))) {
      const start = i;
      while (i < sql.length && /[0-9a-fA-FxX._]/.test(sql[i]!)) i += 1;
      tokens.push({ kind: 'number', text: sql.slice(start, i), start, end: i });
      continue;
    }

    // Word.
    if (isWordStart(ch)) {
      const start = i;
      while (i < sql.length && isWordChar(sql[i]!)) i += 1;
      tokens.push({ kind: 'word', text: sql.slice(start, i), start, end: i });
      continue;
    }

    // Punctuation (two-character operators first).
    const pair = sql.slice(i, i + 2);
    if (pair === '<=' || pair === '>=' || pair === '!=' || pair === '<>' || pair === '||') {
      tokens.push({ kind: 'punct', text: pair, start: i, end: i + 2 });
      i += 2;
      continue;
    }
    tokens.push({ kind: 'punct', text: ch, start: i, end: i + 1 });
    i += 1;
  }

  return tokens;
}

/** Decoded text of every string literal, in order. */
export function stringLiterals(sql: string): string[] {
  return tokenize(sql)
    .filter(token => token.kind === 'string')
    .map(token => token.value ?? '');
}

/**
 * The statement's skeleton: identifiers, literals and numbers are placeholders,
 * keywords keep their spelling, comments are kept as one marker each.
 */
export function normalizedShape(sql: string): string[] {
  return tokenize(sql).map(token => {
    switch (token.kind) {
      case 'string': return '<str>';
      case 'number': return '<num>';
      case 'ident': return '<id>';
      case 'comment': return '<comment>';
      case 'punct': return token.text;
      case 'word': {
        const upper = token.text.toUpperCase();
        return KEYWORDS.has(upper) ? upper : '<id>';
      }
      default: return token.text;
    }
  });
}

/** True when the two statements have the same structure. */
export function sameShape(a: string, b: string): boolean {
  const left = normalizedShape(a);
  const right = normalizedShape(b);
  if (left.length !== right.length) return false;
  return left.every((token, index) => token === right[index]);
}

/** The statement with comments removed; a line comment leaves its newline. */
export function stripComments(sql: string): string {
  const tokens = tokenize(sql);
  let out = '';
  let last = 0;
  for (const token of tokens) {
    if (token.kind !== 'comment') continue;
    out += sql.slice(last, token.start);
    out += token.text.startsWith('/*') ? ' ' : '\n';
    last = token.end;
  }
  return out + sql.slice(last);
}
