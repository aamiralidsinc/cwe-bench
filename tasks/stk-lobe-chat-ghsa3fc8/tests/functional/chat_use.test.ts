import { afterEach, describe, expect, it, vi } from 'vitest';

import { POST as chat } from '@/app/api/chat/[provider]/route';

import { Canary, clientToken, emulateNetwork, RecordedFetch, startCanary } from '../support/harness';

// A correct fix may route its outbound call through a different HTTP client; the emulated network
// below covers either layer, so the legitimate-use checks do not depend on one implementation.
vi.mock('node-fetch', () => ({
  default: (input: any, init?: any) => (globalThis.fetch as any)(input, init),
}));


let canaries: Canary[] = [];
let network: RecordedFetch | undefined;

afterEach(async () => {
  network?.restore();
  network = undefined;
  for (const canary of canaries) await canary.close();
  canaries = [];
  delete process.env.OLLAMA_PROXY_URL;
});

const canary = async () => {
  const started = await startCanary({
    body: '{"message":{"content":"served"},"done":true}\n',
    contentType: 'application/x-ndjson',
  });
  canaries.push(started);
  return started;
};

const chatRequest = (provider: string, payload: Record<string, unknown>) =>
  chat(
    new Request(`https://app.invalid/api/chat/${provider}`, {
      body: JSON.stringify({
        messages: [{ content: 'hello', role: 'user' }],
        model: 'any-model',
        stream: true,
      }),
      headers: {
        'content-type': 'application/json',
        'X-lobe-chat-auth': clientToken(payload),
      },
      method: 'POST',
    }),
    { params: { provider } },
  );

describe('model-service destinations still work for legitimate use', () => {
  it('uses the private service the deployment configured for itself', async () => {
    const selfHosted = await canary();
    process.env.OLLAMA_PROXY_URL = `http://127.0.0.1:${selfHosted.port}`;

    await chatRequest('ollama', { apiKey: 'not-needed' });

    expect(selfHosted.hits.some((hit) => hit.includes('/api/chat'))).toBe(true);
  });

  it('uses a public destination the client chose', async () => {
    network = emulateNetwork({});

    await chatRequest('ollama', { endpoint: 'http://8.8.8.8:11434' });

    expect(network.calls.some((entry) => entry.url.startsWith('http://8.8.8.8:11434'))).toBe(true);
  });
});