import { describe, expect, it } from 'vitest';
import { src, url } from '../support/product.ts';

// Ordinary request-following behaviour that must survive the fix.
describe('the request-following checks keep accepting ordinary values', () => {
  it('follows a public redirect chain that carries no credentials', async () => {
    expect(await src().is_redirect_safe(url('plain.invalid', '/redir'))).toBe(true);
  });

  it('accepts a public URL that does not redirect', async () => {
    expect(await src().is_redirect_safe(url('plain.invalid', '/final'))).toBe(true);
  });

  it('keeps the debug check working for an ordinary reachable URL', async () => {
    expect(await src().is_url_safe_debug(url('plain.invalid', '/final'))).toBe(true);
  });

  it('accepts an ordinary reachable URL with the URL check', async () => {
    expect(await src().is_url_safe(url('plain.invalid', '/final'))).toBe(true);
  });
});
