import { describe, expect, it } from 'vitest';
import { src, credUrl, url } from '../support/product.ts';

// The redirect walker must judge the URL it is given and every target it follows.
describe('the redirect check refuses credentials at every step', () => {
  const cases: Array<[string, string]> = [
    ['the initial URL carries a user name', credUrl('user', 'internal.invalid')],
    ['a target carries a user name', url('safe.invalid', '/hopcred-user')],
    ['a target carries a user name and password', url('safe.invalid', '/hopcred-pass')],
    ['a target carries a password only', url('safe.invalid', '/hopcred-passonly')],
  ];

  for (const [name, target] of cases) {
    it(`refuses when ${name}`, async () => {
      expect(await src().is_redirect_safe(target)).toBe(false);
    });
  }
});
