import { makeTransportMessage } from '../support/fixtures';

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

describe('socket.io notification delivery keeps legitimate destinations', () => {
  it('keeps an absolute web destination and its window target', async () => {
    const notification = await deliver(
      makeTransportMessage({ redirect: { url: 'https://example.com/reports', target: '_blank' } })
    );

    expect(notification.redirect.url).toBe('https://example.com/reports');
    expect(notification.redirect.target).toBe('_blank');
  });

  it('keeps a single-slash relative destination', async () => {
    const notification = await deliver(
      makeTransportMessage({ redirect: { url: '/dashboard', target: '_self' } })
    );

    expect(notification.redirect.url).toBe('/dashboard');
  });

  it('keeps a destination that begins with a template variable', async () => {
    const notification = await deliver(
      makeTransportMessage({ primary: { url: '{{payload.callbackUrl}}', target: '_blank' } })
    );

    expect(notification.primaryAction.redirect.url).toBe('{{payload.callbackUrl}}');
  });

  it('keeps the destination when its window target is not recognised', async () => {
    const notification = await deliver(
      makeTransportMessage({ secondary: { url: '/orders/{{payload.id}}', target: 'attacker-window' } })
    );

    expect(notification.secondaryAction.redirect.url).toBe('/orders/{{payload.id}}');
  });
});
