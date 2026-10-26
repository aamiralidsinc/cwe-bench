import { describe, expect, it } from 'vitest';
import { src } from '../support/product.ts';

// Values the library accepts today that must keep working after the fix.
describe('the URL check keeps accepting ordinary values', () => {
  it('accepts an ordinary public URL', async () => {
    expect(await src().is_url_safe('https://example.com')).toBe(true);
  });

  it('accepts a public URL whose path contains an at-sign', async () => {
    expect(await src().is_url_safe('https://example.com/@alice')).toBe(true);
  });

  it('accepts a public URL whose query contains an at-sign', async () => {
    expect(await src().is_url_safe('https://api.example.com/v1/users?email=a@b.com')).toBe(true);
  });

  it('still refuses a loopback IPv4 address', async () => {
    expect(await src().is_url_safe('http://127.0.0.1/')).toBe(false);
  });

  it('still refuses an IPv6 loopback address', async () => {
    expect(await src().is_url_safe('http://[::1]/')).toBe(false);
  });

  it('keeps the at-sign helper exported and unchanged', () => {
    expect(src().remove_at_symbol_in_string('a@b@c')).toBe('abc');
  });

  it('keeps the protocol decisions unchanged', () => {
    expect(src().is_proto_safe('https:')).toBe(true);
    expect(src().is_proto_safe('ftp:')).toBe(false);
  });

  it('keeps IPv6 detection unchanged', () => {
    expect(src().is_ipv6('::1')).toBe(true);
    expect(src().is_ipv6('127.0.0.1')).toBe(false);
  });
});
