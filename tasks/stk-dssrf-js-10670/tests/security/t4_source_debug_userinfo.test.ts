import { describe, expect, it } from 'vitest';
import { src, credUrl } from '../support/product.ts';

// The verbose public variant must reach the same decision as the main check.
describe('the debug check refuses an authority that carries credentials', () => {
  it('refuses a user name before a named internal host', async () => {
    expect(await src().is_url_safe_debug(credUrl('user', 'internal.invalid'))).toBe(false);
  });

  it('refuses several separators before a named internal host', async () => {
    expect(await src().is_url_safe_debug(credUrl('a@b', 'internal.invalid'))).toBe(false);
  });
});
