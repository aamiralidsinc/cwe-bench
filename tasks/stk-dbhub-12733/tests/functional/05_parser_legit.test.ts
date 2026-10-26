import { describe, it, expect } from 'vitest';
import { splitSQLStatements, stripCommentsAndStrings } from '../../src/utils/sql-parser.js';
import { isReadOnlySQL } from '../../src/utils/allowed-keywords.js';

describe('ordinary statement and comment parsing keeps working', () => {
  it('keeps a double-dash comment with whitespace and semicolons inside it', () => {
    expect(splitSQLStatements('SELECT 1 -- this; has; semicolons\n; SELECT 2')).toHaveLength(2);
    expect(splitSQLStatements('SELECT 1 -- c;DROP TABLE t', 'mysql')).toHaveLength(1);
    expect(splitSQLStatements('SELECT 1 -- c;DROP TABLE t', 'mariadb')).toHaveLength(1);
  });

  it('keeps a control character after two dashes a comment', () => {
    expect(splitSQLStatements('SELECT 1 --\x7Fc;DROP TABLE t', 'mysql')).toHaveLength(1);
  });

  it('keeps two dashes an ordinary comment in PostgreSQL', () => {
    expect(splitSQLStatements('SELECT 1--1;DROP TABLE t', 'postgres')).toHaveLength(1);
  });

  it('keeps semicolons inside block comments and quoted text', () => {
    expect(splitSQLStatements('SELECT 1 /* semi; colon */ ; SELECT 2', 'mysql')).toHaveLength(2);
    expect(splitSQLStatements("SELECT 'a;b'", 'mysql')).toHaveLength(1);
    expect(splitSQLStatements('SELECT * FROM `a;b`', 'mysql')).toHaveLength(1);
  });

  it('keeps executable conditional comments executable', () => {
    expect(stripCommentsAndStrings('/*!50000 DELETE FROM users */', 'mysql')).toContain('DELETE');
    expect(stripCommentsAndStrings('/*M! DROP TABLE users */', 'mariadb')).toContain('DROP');
    expect(isReadOnlySQL('/*!50000 DELETE FROM users */', 'mysql')).toBe(false);
    expect(isReadOnlySQL('/*M! DROP TABLE users */', 'mariadb')).toBe(false);
  });

  it('keeps function calls inside a SELECT read-only', () => {
    expect(isReadOnlySQL("SELECT REPLACE(name, 'a', 'b') FROM users", 'mysql')).toBe(true);
    expect(isReadOnlySQL("WITH cte AS (SELECT REPLACE(name, 'a', 'b') AS n FROM users) SELECT * FROM cte", 'mysql')).toBe(true);
  });
});
