import { describe, expect, it } from 'vitest';
import { src, credUrl } from '../support/product.ts';

// The reported route: a public URL check that approves an authority carrying credentials.
describe('the URL check refuses an authority that carries credentials', () => {
  const cases: Array<[string, string]> = [
    ['a user name before a local host', 'http://user@localhost/'],
    ['a user name before a named internal host', credUrl('user', 'internal.invalid')],
    ['several separators before a named internal host', credUrl('a@b', 'internal.invalid')],
    ['a fullwidth separator before a local host', 'http://user＠localhost/'],
  ];

  for (const [name, target] of cases) {
    it(`refuses ${name}`, async () => {
      expect(await src().is_url_safe(target)).toBe(false);
    });
  }
});
