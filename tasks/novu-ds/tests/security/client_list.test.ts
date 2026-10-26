import { makeNotificationPayload } from '../support/fixtures';
import { assertSafeNotification } from '../support/safe';

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

describe('notification listing', () => {
  it('does not present a script-scheme destination from the listing', async () => {
    const notification = await list(
      makeNotificationPayload({ redirect: { url: 'javascript:alert(1)', target: '_blank' } })
    );

    assertSafeNotification(notification);
  });

  it('does not present a protocol-relative destination from the listing', async () => {
    const notification = await list(
      makeNotificationPayload({ primary: { url: '//attacker.example/collect', target: '_blank' } })
    );

    assertSafeNotification(notification);
  });

  it('does not present a document-scheme destination on a listed action', async () => {
    const notification = await list(
      makeNotificationPayload({
        secondary: { url: 'data:text/html,<script>alert(1)</script>', target: '_self' },
      })
    );

    assertSafeNotification(notification);
  });

  it('does not present an unsupported window target from the listing', async () => {
    const notification = await list(
      makeNotificationPayload({ redirect: { url: 'https://example.com/ok', target: 'attacker-window' } })
    );

    assertSafeNotification(notification);
  });
});
