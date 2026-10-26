import { describe, it, expect } from 'vitest';
import { isReadOnlySQL } from '../../src/utils/allowed-keywords.js';

describe('the read-only decision still accepts legitimate statements', () => {
  it('accepts ordinary queries', () => {
    expect(isReadOnlySQL('SELECT * FROM users', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('SELECT REPLACE(name, \'a\', \'b\') FROM users', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('WITH cte AS (SELECT 1) SELECT * FROM cte', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('EXPLAIN DELETE FROM users', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('EXPLAIN ANALYZE SELECT * FROM users', 'postgres')).toBe(true);
    expect(isReadOnlySQL('SELECT 1', 'postgres')).toBe(true);
    expect(isReadOnlySQL('SELECT 1', 'mysql')).toBe(true);
    expect(isReadOnlySQL('SHOW TABLES', 'mysql')).toBe(true);
    expect(isReadOnlySQL('DESCRIBE users', 'mysql')).toBe(true);
  });

  it('accepts the introspection pragmas that take a name', () => {
    expect(isReadOnlySQL('PRAGMA table_info(users)', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('PRAGMA index_info(users)', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('PRAGMA index_list(users)', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('PRAGMA foreign_key_list(orders)', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('PRAGMA main.table_info(users)', 'sqlite')).toBe(true);
  });

  it('accepts the pragmas that read a value', () => {
    expect(isReadOnlySQL('PRAGMA user_version', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('PRAGMA journal_mode', 'sqlite')).toBe(true);
    expect(isReadOnlySQL('PRAGMA application_id', 'sqlite')).toBe(true);
  });

  it('still rejects statements that are plainly writes', () => {
    expect(isReadOnlySQL('INSERT INTO users VALUES (1)', 'sqlite')).toBe(false);
    expect(isReadOnlySQL('UPDATE users SET name = 1', 'sqlite')).toBe(false);
    expect(isReadOnlySQL('DELETE FROM users', 'sqlite')).toBe(false);
    expect(isReadOnlySQL('DROP TABLE users', 'sqlite')).toBe(false);
    expect(isReadOnlySQL('SELECT * INTO backup FROM users', 'sqlite')).toBe(false);
    expect(isReadOnlySQL('WITH cte AS (UPDATE users SET name = 1 RETURNING *) SELECT * FROM cte', 'sqlite')).toBe(false);
  });
});
