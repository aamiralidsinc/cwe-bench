import { makePreviewPayload } from '../support/fixtures';
import { assertSafePreview } from '../support/safe';

async function preview(payload: any) {
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
      previewNotification: async () => payload,
    },
    eventEmitterInstance: new NovuEventEmitter(),
  });

  const result = await notifications.preview('notification-1');

  return result.data;
}

describe('notification preview model', () => {
  it('does not present a script-scheme destination on the preview', async () => {
    const result = await preview(
      makePreviewPayload({ redirect: { url: 'javascript:alert(1)', target: '_blank' } })
    );

    assertSafePreview(result);
  });

  it('does not present a protocol-relative destination on a preview action', async () => {
    const result = await preview(
      makePreviewPayload({ primary: { url: '//attacker.example/collect', target: '_blank' } })
    );

    assertSafePreview(result);
  });

  it('does not present an unsupported window target on the preview', async () => {
    const result = await preview(
      makePreviewPayload({ redirect: { url: 'https://example.com/ok', target: 'attacker-window' } })
    );

    assertSafePreview(result);
  });
});
