/**
 * Evaluates the WHERE clause of a generated statement against in-memory rows.
 *
 * The tests use it to ask what a statement means, rather than what it looks
 * like: the clause is parsed with SQL operator precedence (AND binds tighter
 * than OR) and comments are honoured, so a statement that lets one condition
 * change another's reach is visible as a wrong row set.
 *
 * Only the shapes the query builder emits for plain column conditions are
 * supported: comparisons, IS [NOT] NULL, IN, NOT IN, LIKE, NOT LIKE, BETWEEN,
 * AND, OR, NOT and parentheses.
 */
import { stripComments, tokenize, type Token } from './sqlcheck.js';

export type Row = Record<string, unknown>;

const CLAUSE_END = new Set([
  'GROUP', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'FORMAT', 'UNION', 'SETTINGS', 'PREWHERE',
]);

/** Tokens of a top-level clause (WHERE or HAVING), or [] when absent. */
export function clauseTokens(sql: string, keyword: 'WHERE' | 'HAVING'): Token[] {
  const all = tokenize(stripComments(sql));
  let depth = 0;
  let start = -1;
  for (let i = 0; i < all.length; i += 1) {
    const token = all[i]!;
    if (token.kind === 'punct' && token.text === '(') depth += 1;
    if (token.kind === 'punct' && token.text === ')') depth -= 1;
    if (depth === 0 && token.kind === 'word' && token.text.toUpperCase() === keyword) {
      start = i + 1;
      break;
    }
  }
  if (start < 0) return [];
  const out: Token[] = [];
  depth = 0;
  for (let i = start; i < all.length; i += 1) {
    const token = all[i]!;
    if (token.kind === 'punct' && token.text === '(') depth += 1;
    if (token.kind === 'punct' && token.text === ')') depth -= 1;
    if (depth === 0 && token.kind === 'word' && CLAUSE_END.has(token.text.toUpperCase())) break;
    out.push(token);
  }
  return out;
}

class Parser {
  private i = 0;

  constructor(private readonly tokens: Token[], private readonly row: Row) {}

  private peek(): Token | undefined {
    return this.tokens[this.i];
  }

  private next(): Token {
    const token = this.tokens[this.i];
    if (!token) throw new Error('Unexpected end of WHERE clause');
    this.i += 1;
    return token;
  }

  private isWord(value: string): boolean {
    const token = this.peek();
    return !!token && token.kind === 'word' && token.text.toUpperCase() === value;
  }

  private isPunct(value: string): boolean {
    const token = this.peek();
    return !!token && token.kind === 'punct' && token.text === value;
  }

  parse(): boolean {
    const value = this.parseOr();
    if (this.i !== this.tokens.length) {
      throw new Error(`Trailing SQL in WHERE clause: ${this.tokens.slice(this.i).map(t => t.text).join(' ')}`);
    }
    return value;
  }

  private parseOr(): boolean {
    let value = this.parseAnd();
    while (this.isWord('OR')) {
      this.next();
      const right = this.parseAnd();
      value = value || right;
    }
    return value;
  }

  private parseAnd(): boolean {
    let value = this.parseNot();
    while (this.isWord('AND')) {
      this.next();
      const right = this.parseNot();
      value = value && right;
    }
    return value;
  }

  private parseNot(): boolean {
    if (this.isWord('NOT')) {
      this.next();
      return !this.parseNot();
    }
    return this.parseAtom();
  }

  private parseAtom(): boolean {
    if (this.isPunct('(')) {
      this.next();
      const value = this.parseOr();
      if (!this.isPunct(')')) throw new Error('Missing closing parenthesis in WHERE clause');
      this.next();
      return value;
    }
    return this.parsePredicate();
  }

  private parsePredicate(): boolean {
    const left = this.parseOperand();

    if (this.isWord('IS')) {
      this.next();
      const negated = this.isWord('NOT');
      if (negated) this.next();
      if (!this.isWord('NULL')) throw new Error('Expected NULL after IS');
      this.next();
      const isNull = left === null || left === undefined;
      return negated ? !isNull : isNull;
    }

    if (this.isWord('NOT') || this.isWord('IN') || this.isWord('LIKE') || this.isWord('BETWEEN')) {
      let negated = false;
      if (this.isWord('NOT')) { negated = true; this.next(); }
      if (this.isWord('IN')) {
        this.next();
        if (!this.isPunct('(')) throw new Error('Expected ( after IN');
        this.next();
        const values: unknown[] = [];
        while (!this.isPunct(')')) {
          values.push(this.parseOperand());
          if (this.isPunct(',')) { this.next(); continue; }
        }
        this.next();
        const hit = values.some(value => value === left);
        return negated ? !hit : hit;
      }
      if (this.isWord('LIKE')) {
        this.next();
        const pattern = this.parseOperand();
        const hit = like(String(left ?? ''), String(pattern ?? ''));
        return negated ? !hit : hit;
      }
      if (this.isWord('BETWEEN')) {
        this.next();
        const low = this.parseOperand();
        if (!this.isWord('AND')) throw new Error('Expected AND in BETWEEN');
        this.next();
        const high = this.parseOperand();
        const hit = Number(left) >= Number(low) && Number(left) <= Number(high);
        return negated ? !hit : hit;
      }
      throw new Error('Unsupported negated predicate');
    }

    const operator = this.peek();
    if (operator && operator.kind === 'punct' && ['=', '!=', '<>', '<', '>', '<=', '>='].includes(operator.text)) {
      this.next();
      const right = this.parseOperand();
      switch (operator.text) {
        case '=': return left === right;
        case '!=':
        case '<>': return left !== right;
        case '<': return Number(left) < Number(right);
        case '>': return Number(left) > Number(right);
        case '<=': return Number(left) <= Number(right);
        case '>=': return Number(left) >= Number(right);
      }
    }

    return Boolean(left);
  }

  private parseOperand(): unknown {
    const token = this.next();
    if (token.kind === 'string') return token.value ?? '';
    if (token.kind === 'number') return Number(token.text);
    if (token.kind === 'ident') return this.lookup(token.value ?? token.text);
    if (token.kind === 'punct' && token.text === '-') {
      const number = this.next();
      return -Number(number.text);
    }
    if (token.kind === 'word') {
      const upper = token.text.toUpperCase();
      if (upper === 'NULL') return null;
      if (upper === 'TRUE') return true;
      if (upper === 'FALSE') return false;
      return this.lookup(token.text);
    }
    throw new Error(`Unexpected token in WHERE clause: ${token.text}`);
  }

  private lookup(name: string): unknown {
    const trimmed = name.replace(/^`|`$/g, '').replace(/^"|"$/g, '');
    if (Object.prototype.hasOwnProperty.call(this.row, trimmed)) return this.row[trimmed];
    const last = trimmed.split('.').pop() as string;
    if (Object.prototype.hasOwnProperty.call(this.row, last)) return this.row[last];
    return undefined;
  }
}

function like(value: string, pattern: string): boolean {
  const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`^${escaped.replace(/%/g, '.*').replace(/_/g, '.')}$`, 's');
  return regex.test(value);
}

/** Evaluate a clause of the statement against one row. */
export function evaluateClause(sql: string, keyword: 'WHERE' | 'HAVING', row: Row): boolean {
  const tokens = clauseTokens(sql, keyword);
  if (tokens.length === 0) return true;
  return new Parser(tokens, row).parse();
}

/** Evaluate the statement's WHERE clause against one row. */
export function evaluateWhere(sql: string, row: Row): boolean {
  return evaluateClause(sql, 'WHERE', row);
}

/** The rows a statement's WHERE clause keeps. */
export function filterRows(sql: string, rows: Row[]): Row[] {
  return rows.filter(row => evaluateWhere(sql, row));
}

/** The rows a statement's HAVING clause keeps (evaluated over result rows). */
export function filterHaving(sql: string, rows: Row[]): Row[] {
  return rows.filter(row => evaluateClause(sql, 'HAVING', row));
}
