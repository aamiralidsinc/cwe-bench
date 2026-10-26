import { makeTransportMessage } from '../support/fixtures';

const mockPartyInstances: any[] = [];

jest.mock('partysocket', () => {
  class MockWebSocket {
    listeners: Record<string, Function[]> = {};
    readyState = 1;
    url: string;

    constructor(url: string) {
      this.url = url;
      mockPartyInstances.push(this);
    }

    addEventListener(event: string, callback: Function) {
      (this.listeners[event] = this.listeners[event] || []).push(callback);
    }

    send() {}

    close() {}

    emitFrame(payload: any) {
      (this.listeners['message'] || []).forEach((callback) => callback({ data: JSON.stringify(payload) }));
    }
  }

  return { __esModule: true, WebSocket: MockWebSocket };
});

async function deliver(message: any) {
  // Required inside the test so a missing or unloadable product module fails the test rather
  // than making the whole file vanish from the result set.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { NovuEventEmitter } = require('@product/packages/js/src/event-emitter');
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { PartySocketClient } = require('@product/packages/js/src/ws/party-socket');

  const emitter = new NovuEventEmitter();
  const socket = new PartySocketClient({
    inboxServiceInstance: { isSessionInitialized: true },
    eventEmitterInstance: emitter,
  });

  const received: any[] = [];
  emitter.on('notifications.notification_received', (event: any) => received.push(event.result));
  emitter.emit('session.initialize.resolved', { data: { token: 'test-token' } });
  await socket.connect();

  const instance = mockPartyInstances[mockPartyInstances.length - 1];
  instance.emitFrame({ event: 'notification_received', data: { message } });
  await new Promise((resolve) => setTimeout(resolve, 0));

  return received[0];
}

describe('party socket notification delivery keeps legitimate destinations', () => {
  it('keeps an absolute web destination and its window target', async () => {
    const notification = await deliver(
      makeTransportMessage({ redirect: { url: 'http://example.com/reports', target: '_blank' } })
    );

    expect(notification.redirect.url).toBe('http://example.com/reports');
    expect(notification.redirect.target).toBe('_blank');
  });

  it('keeps a single-slash relative destination', async () => {
    const notification = await deliver(
      makeTransportMessage({ primary: { url: '/dashboard', target: '_self' } })
    );

    expect(notification.primaryAction.redirect.url).toBe('/dashboard');
  });

  it('keeps template variables inside an absolute destination', async () => {
    const notification = await deliver(
      makeTransportMessage({ redirect: { url: 'https://example.com/orders/{{payload.orderId}}', target: '_blank' } })
    );

    expect(notification.redirect.url).toBe('https://example.com/orders/{{payload.orderId}}');
  });

  it('keeps the destination when its window target is not recognised', async () => {
    const notification = await deliver(
      makeTransportMessage({ primary: { url: 'https://example.com/ok', target: 'attacker-window' } })
    );

    expect(notification.primaryAction.redirect.url).toBe('https://example.com/ok');
  });
});
