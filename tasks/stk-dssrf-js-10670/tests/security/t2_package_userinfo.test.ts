import { describe, expect, it } from 'vitest';
import { pkg, credUrl, url } from '../support/product.ts';

// The same adjudication reached through the package entry a consumer loads.
describe('the package entry refuses an authority that carries credentials', () => {
  it('refuses a user name before a local host', async () => {
    expect(await pkg().is_url_safe('http://user@localhost/')).toBe(false);
  });

  it('refuses a user name before a named internal host', async () => {
    expect(await pkg().is_url_safe(credUrl('user', 'internal.invalid'))).toBe(false);
  });

  it('refuses a redirect whose initial URL carries a user name', async () => {
    expect(await pkg().is_redirect_safe(credUrl('user', 'internal.invalid'))).toBe(false);
  });

  it('refuses a redirect target that carries a user name', async () => {
    expect(await pkg().is_redirect_safe(url('safe.invalid', '/hopcred-user'))).toBe(false);
  });

  it('refuses a debug-check URL that carries a user name', async () => {
    expect(await pkg().is_url_safe_debug(credUrl('user', 'internal.invalid'))).toBe(false);
  });
});
