import { afterEach, describe, expect, it } from 'vitest';

import { POST as chat } from '@/app/api/chat/[provider]/route';

import { Canary, clientToken, isClientError, startCanary } from '../support/harness';

let canaries: Canary[] = [];

afterEach(async () => {
  for (const canary of canaries) await canary.close();
  canaries = [];
});

const canary = async () => {
  const started = await startCanary({
    body: '{"message":{"content":"internal"},"done":true}\n',
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

describe('a model-service destination carried by the caller', () => {
  it('does not connect to a loopback address given for a self-hosted model service', async () => {
    const internal = await canary();

    const response = await chatRequest('ollama', { endpoint: `http://127.0.0.1:${internal.port}` });

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });

  it('does not connect to a loopback address given for an OpenAI-compatible service', async () => {
    const internal = await canary();

    const response = await chatRequest('openai', {
      apiKey: 'sk-test',
      endpoint: `http://127.0.0.1:${internal.port}/v1`,
    });

    expect(internal.hits).toEqual([]);
    expect(isClientError(response.status)).toBe(true);
  });
});
