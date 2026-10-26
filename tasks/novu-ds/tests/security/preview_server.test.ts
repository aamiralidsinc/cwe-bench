import { makeMessageEntity } from '../support/fixtures';
import { assertSafePreview } from '../support/safe';

async function preview(parts: Parameters<typeof makeMessageEntity>[0]) {
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

describe('notification preview payloads', () => {
  it('does not present a script-scheme destination on the preview', async () => {
    const result = await preview({ redirect: { url: 'javascript:alert(1)', target: '_blank' } });

    assertSafePreview(result);
  });

  it('does not present a protocol-relative destination on a preview action', async () => {
    const result = await preview({
      primary: { url: '//attacker.example/collect', target: '_blank' },
    });

    assertSafePreview(result);
  });

  it('does not present a document-scheme destination on a preview action', async () => {
    const result = await preview({
      secondary: { url: 'data:text/html,<script>alert(1)</script>', target: '_self' },
    });

    assertSafePreview(result);
  });
});
