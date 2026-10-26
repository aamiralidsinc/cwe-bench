import { makeMessageEntity } from '../support/fixtures';
import { assertSafeNotification } from '../support/safe';

function mapped(parts: Parameters<typeof makeMessageEntity>[0]) {
  // Required inside the test so a missing or unloadable product module fails the test rather
  // than making the whole file vanish from the result set.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { mapToDto } = require('@product/apps/api/src/app/inbox/utils/notification-mapper');

  return mapToDto(makeMessageEntity(parts));
}

describe('inbox API response payloads', () => {
  it('does not present a script-scheme destination on the notification', () => {
    const dto = mapped({ redirect: { url: 'javascript:alert(1)', target: '_blank' } });

    assertSafeNotification(dto);
  });

  it('does not present a document-scheme destination on a primary action', () => {
    const dto = mapped({
      primary: { url: 'data:text/html,<script>alert(1)</script>', target: '_blank' },
    });

    assertSafeNotification(dto);
  });

  it('does not present a script-scheme destination on a secondary action', () => {
    const dto = mapped({ secondary: { url: 'vbscript:msgbox(1)', target: '_self' } });

    assertSafeNotification(dto);
  });

  it('does not present a protocol-relative destination as a relative path', () => {
    const dto = mapped({ redirect: { url: '//attacker.example/collect', target: '_blank' } });

    assertSafeNotification(dto);
  });

  it('does not present a protocol-relative destination on an action', () => {
    const dto = mapped({ primary: { url: '///attacker.example/collect', target: '_blank' } });

    assertSafeNotification(dto);
  });

  it('does not present a non-web scheme destination', () => {
    const dto = mapped({ redirect: { url: 'mailto:someone@example.com', target: '_blank' } });

    assertSafeNotification(dto);
  });

  it('does not present an unsupported window target', () => {
    const dto = mapped({ redirect: { url: 'https://example.com/ok', target: 'attacker-window' } });

    assertSafeNotification(dto);
  });
});
