import { makeMessageEntity } from '../support/fixtures';

function mapped(parts: Parameters<typeof makeMessageEntity>[0]) {
  // Required inside the test so a missing or unloadable product module fails the test rather
  // than making the whole file vanish from the result set.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { mapToDto } = require('@product/apps/api/src/app/inbox/utils/notification-mapper');

  return mapToDto(makeMessageEntity(parts));
}

describe('inbox API response payloads keep legitimate destinations', () => {
  it('keeps an absolute web destination and its window target', () => {
    const dto = mapped({ redirect: { url: 'https://example.com/reports?id=42', target: '_blank' } });

    expect(dto.redirect.url).toBe('https://example.com/reports?id=42');
    expect(dto.redirect.target).toBe('_blank');
  });

  it('keeps a single-slash relative destination', () => {
    const dto = mapped({ redirect: { url: '/dashboard', target: '_self' } });

    expect(dto.redirect.url).toBe('/dashboard');
    expect(dto.redirect.target).toBe('_self');
  });

  it('keeps a destination that begins with a template variable', () => {
    const dto = mapped({ redirect: { url: '{{payload.callbackUrl}}', target: '_blank' } });

    expect(dto.redirect.url).toBe('{{payload.callbackUrl}}');
  });

  it('keeps template variables inside an absolute destination', () => {
    const dto = mapped({ redirect: { url: 'https://example.com/orders/{{payload.orderId}}', target: '_blank' } });

    expect(dto.redirect.url).toBe('https://example.com/orders/{{payload.orderId}}');
  });

  it('keeps template variables inside a relative destination', () => {
    const dto = mapped({ primary: { url: '/orders/{{payload.orderId}}', target: '_self' } });

    expect(dto.primaryAction.redirect.url).toBe('/orders/{{payload.orderId}}');
  });

  it('keeps the destination when its window target is not recognised', () => {
    const dto = mapped({ redirect: { url: 'https://example.com/ok', target: 'attacker-window' } });

    expect(dto.redirect.url).toBe('https://example.com/ok');
  });

  it('keeps every action destination and the notification destination together', () => {
    const dto = mapped({
      redirect: { url: 'https://example.com/notification', target: '_blank' },
      primary: { url: '/primary', target: '_self' },
      secondary: { url: 'https://example.com/secondary', target: '_parent' },
    });

    expect(dto.redirect.url).toBe('https://example.com/notification');
    expect(dto.primaryAction.redirect.url).toBe('/primary');
    expect(dto.secondaryAction.redirect.url).toBe('https://example.com/secondary');
    expect(dto.secondaryAction.redirect.target).toBe('_parent');
  });

  it('keeps a notification without a destination free of one', () => {
    const dto = mapped({});

    expect(dto.redirect).toBeUndefined();
  });
});
