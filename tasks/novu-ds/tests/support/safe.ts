// Test-local oracle for what a subscriber may be asked to navigate to. It is deliberately
// independent of any product code: a hardened or refactored helper must not change it.

export const SUPPORTED_TARGETS = ['_self', '_blank', '_parent', '_top', '_unfencedTop'];

export function isSafeDestination(url: unknown): boolean {
  if (url === undefined || url === null) return true;
  if (typeof url !== 'string') return false;
  if (url.length === 0) return true;

  // A destination may begin with a template variable; the compiled value is what matters later.
  if (/^\{\{[^}]*\}\}/.test(url)) return true;

  if (/^https?:\/\//i.test(url)) {
    // absolute web address with a host; a third slash after the scheme is not a host
    return /^https?:\/\/[^\s/$.?#][^\s]*$/i.test(url);
  }

  if (url.startsWith('/')) {
    // exactly one leading slash; two or more start a network-path reference to another host
    return !url.startsWith('//') && !/\s/.test(url);
  }

  return false;
}

export function assertSafeRedirect(redirect: any): void {
  if (redirect === undefined || redirect === null) return;

  expect(isSafeDestination(redirect.url)).toBe(true);
  if (redirect.target !== undefined) {
    expect(SUPPORTED_TARGETS).toContain(redirect.target);
  }
}

export function assertSafeNotification(notification: any): void {
  expect(notification).toBeTruthy();
  assertSafeRedirect(notification.redirect);
  assertSafeRedirect(notification.primaryAction && notification.primaryAction.redirect);
  assertSafeRedirect(notification.secondaryAction && notification.secondaryAction.redirect);
}

export function assertSafePreview(preview: any): void {
  assertSafeNotification(preview);
}
