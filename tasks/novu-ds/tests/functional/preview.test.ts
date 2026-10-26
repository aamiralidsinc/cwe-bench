import { makeMessageEntity, makePreviewPayload } from '../support/fixtures';

async function serverPreview(parts: Parameters<typeof makeMessageEntity>[0]) {
  // Required inside the test so a missing or unloadable product module fails the test rather
  // than making the whole file vanish from the result set.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const {
    GetNotificationPreview,
  } = require('@product/apps/api/src/app/inbox/usecases/get-notification-preview/get-notification-preview.usecase');

  const usecase = new GetNotificationPreview({
    findOneForInbox: async () => makeMessageEntity(parts),
  });

  return usecase.execute({
    environmentId: 'environment-1',
    organizationId: 'organization-1',
    subscriberId: 'subscriber-internal-1',
    notificationId: 'message-1',
  });
}

async function clientPreview(payload: any) {
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

describe('notification previews keep legitimate destinations', () => {
  it('keeps an absolute web destination on a preview', async () => {
    const result = await serverPreview({ redirect: { url: 'https://example.com/reports', target: '_blank' } });

    expect(result.redirect.url).toBe('https://example.com/reports');
    expect(result.redirect.target).toBe('_blank');
  });

  it('keeps a single-slash relative destination on a preview action', async () => {
    const result = await serverPreview({ primary: { url: '/dashboard', target: '_self' } });

    expect(result.primaryAction.redirect.url).toBe('/dashboard');
  });

  it('keeps a destination that begins with a template variable on a preview', async () => {
    const result = await serverPreview({ secondary: { url: '{{payload.callbackUrl}}', target: '_blank' } });

    expect(result.secondaryAction.redirect.url).toBe('{{payload.callbackUrl}}');
  });

  it('keeps the client preview destination when its window target is not recognised', async () => {
    const result = await clientPreview(
      makePreviewPayload({ redirect: { url: '/orders/{{payload.id}}', target: 'attacker-window' } })
    );

    expect(result.redirect.url).toBe('/orders/{{payload.id}}');
  });

  it('keeps a client preview without a destination free of one', async () => {
    const result = await clientPreview(makePreviewPayload({}));

    expect(result.redirect).toBeUndefined();
  });
});
