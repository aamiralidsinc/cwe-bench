import { makeTransportMessage } from '../support/fixtures';
import { assertSafeNotification } from '../support/safe';

const mockHandlers: Record<string, Function[]> = {};
const mockFakeSocket = {
  on: jest.fn((event: string, callback: Function) => {
    (mockHandlers[event] = mockHandlers[event] || []).push(callback);
  }),
  disconnect: jest.fn(),
};

jest.mock('socket.io-client', () => {
  const io = jest.fn(() => mockFakeSocket);
  return { __esModule: true, default: io, __handlers: mockHandlers };
});

async function deliver(message: any) {
  // Required inside the test so a missing or unloadable product module fails the test rather
  // than making the whole file vanish from the result set.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { NovuEventEmitter } = require('@product/packages/js/src/event-emitter');
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { Socket } = require('@product/packages/js/src/ws/socket');

  const emitter = new NovuEventEmitter();
  const socket = new Socket({
    inboxServiceInstance: { isSessionInitialized: true },
    eventEmitterInstance: emitter,
  });

  const received: any[] = [];
  emitter.on('notifications.notification_received', (event: any) => received.push(event.result));
  emitter.emit('session.initialize.resolved', { data: { token: 'test-token' } });
  await socket.connect();

  const handlers = mockHandlers['notification_received'];
  handlers[handlers.length - 1]({ message });
  await new Promise((resolve) => setTimeout(resolve, 0));

  return received[0];
}

describe('socket.io notification delivery', () => {
  it('does not present a script-scheme destination', async () => {
    const notification = await deliver(
      makeTransportMessage({ redirect: { url: 'javascript:alert(1)', target: '_blank' } })
    );

    assertSafeNotification(notification);
  });

  it('does not present a protocol-relative destination as a relative path', async () => {
    const notification = await deliver(
      makeTransportMessage({ primary: { url: '//attacker.example/collect', target: '_blank' } })
    );

    assertSafeNotification(notification);
  });

  it('does not present a document-scheme destination on an action', async () => {
    const notification = await deliver(
      makeTransportMessage({
        secondary: { url: 'data:text/html,<script>alert(1)</script>', target: '_self' },
      })
    );

    assertSafeNotification(notification);
  });

  it('does not present an unsupported window target', async () => {
    const notification = await deliver(
      makeTransportMessage({ primary: { url: 'https://example.com/ok', target: 'attacker-window' } })
    );

    assertSafeNotification(notification);
  });
});
