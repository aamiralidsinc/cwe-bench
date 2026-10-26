import { makeNotificationPayload } from '../support/fixtures';

async function list(payload: any) {
  // Required inside the test so a missing or unloadable product module fails the test rather
  // than making the whole file vanish from the result set.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { Notifications } = require('@product/packages/js/src/notifications/notifications');
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { NovuEventEmitter } = require('@product/packages/js/src/event-emitter');

  const notifications = new Notifications({
    useCache: false,
    inboxServiceInstance: {
      isSessionInitialized: true,
      fetchNotifications: async () => ({ data: [payload], hasMore: false, filter: {} }),
    },
    eventEmitterInstance: new NovuEventEmitter(),
  });

  const result = await notifications.list({ limit: 10 });

  return result.data.notifications[0];
}

describe('notification listing keeps legitimate destinations', () => {
  it('keeps an absolute web destination and its window target', async () => {
    const notification = await list(
      makeNotificationPayload({ redirect: { url: 'https://example.com/reports', target: '_blank' } })
    );

    expect(notification.redirect.url).toBe('https://example.com/reports');
    expect(notification.redirect.target).toBe('_blank');
  });

  it('keeps a single-slash relative destination', async () => {
    const notification = await list(
      makeNotificationPayload({ primary: { url: '/dashboard', target: '_self' } })
    );

    expect(notification.primaryAction.redirect.url).toBe('/dashboard');
  });

  it('keeps a destination that begins with a template variable', async () => {
    const notification = await list(
      makeNotificationPayload({ secondary: { url: '{{payload.callbackUrl}}', target: '_blank' } })
    );

    expect(notification.secondaryAction.redirect.url).toBe('{{payload.callbackUrl}}');
  });

  it('keeps the destination when its window target is not recognised', async () => {
    const notification = await list(
      makeNotificationPayload({ redirect: { url: '/orders/{{payload.id}}', target: 'attacker-window' } })
    );

    expect(notification.redirect.url).toBe('/orders/{{payload.id}}');
  });

  it('keeps a notification without a destination free of one', async () => {
    const notification = await list(makeNotificationPayload({}));

    expect(notification.redirect).toBeUndefined();
  });
});
