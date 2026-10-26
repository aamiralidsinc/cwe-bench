import { describe, expect, it } from 'vitest';
import { pkg, url } from '../support/product.ts';

// The same legitimate values through the entry the package exposes to consumers.
describe('the package entry keeps accepting ordinary values', () => {
  it('accepts an ordinary public URL', async () => {
    expect(await pkg().is_url_safe('https://example.com')).toBe(true);
  });

  it('accepts a public URL whose path contains an at-sign', async () => {
    expect(await pkg().is_url_safe('https://example.com/@alice')).toBe(true);
  });

  it('accepts a public URL whose query contains an at-sign', async () => {
    expect(await pkg().is_url_safe('https://api.example.com/v1/users?email=a@b.com')).toBe(true);
  });

  it('keeps the at-sign helper exported and unchanged', () => {
    expect(pkg().remove_at_symbol_in_string('a@b')).toBe('ab');
  });

  it('follows a public redirect chain that carries no credentials', async () => {
    expect(await pkg().is_redirect_safe(url('plain.invalid', '/redir'))).toBe(true);
  });

  it('keeps the debug check working for an ordinary reachable URL', async () => {
    expect(await pkg().is_url_safe_debug(url('plain.invalid', '/final'))).toBe(true);
  });
});
