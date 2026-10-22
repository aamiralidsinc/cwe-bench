'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { LanguageModelService } = require('@theia/ai-core/lib/common/language-model-service');
const { LanguageModelRegistry } = require('@theia/ai-core/lib/common/language-model');
const {
    PREFERENCE_NAME_REQUEST_SETTINGS,
    PREFERENCE_NAME_THINKING_MODE
} = require('@theia/ai-core/lib/common/ai-core-preferences');

function makeModel(calls) {
    return {
        id: 'anthropic/claude-test',
        name: 'test',
        request: async (request) => {
            calls.push(request);
            return { type: 'text', text: 'ok' };
        }
    };
}

function makeRequest() {
    return {
        messages: [{ actor: 'user', type: 'text', text: 'hello' }],
        requestId: 'request-1',
        sessionId: 'session-1',
        agentId: 'test-agent'
    };
}

function buildService(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    h.bindInfrastructure(container, { preferences, trust });
    h.bind(container, LanguageModelRegistry, {
        onLanguageModelUpdated: () => undefined,
        onLanguageModelAdded: () => h.disposable(),
        onLanguageModelRemoved: () => h.disposable()
    });
    return container.get(LanguageModelService);
}

describe('language model requests in an untrusted workspace', () => {
    it('are refused before reaching the provider and leave no session behind', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const service = buildService(preferences, trust);
        const calls = [];

        await assert.rejects(service.sendRequest(makeModel(calls), makeRequest()));
        assert.strictEqual(calls.length, 0, 'the model provider must not be called');
        assert.strictEqual(service.sessions.length, 0, 'no request may be recorded');
    });

    it('do not reach the provider while the trust state is unresolved', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust();
        const service = buildService(preferences, trust);
        const calls = [];

        const outcome = await Promise.race([
            service.sendRequest(makeModel(calls), makeRequest()).then(() => 'resolved', () => 'rejected'),
            h.flush(4).then(() => 'pending')
        ]);

        assert.strictEqual(calls.length, 0, 'the model provider must not be called');
        assert.strictEqual(service.sessions.length, 0, 'no request may be recorded');
        // Refusing at once (rejected) and waiting for the trust state (pending) are both
        // fail-closed; succeeding is not.
        assert.notStrictEqual(outcome, 'resolved', 'an unresolved trust state must not let the request succeed');
    });

    it('cannot be bypassed by gaining trust and losing it between requests', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const service = buildService(preferences, trust);
        const calls = [];

        await assert.rejects(service.sendRequest(makeModel(calls), makeRequest()));
        trust.set(true);
        await h.flush(2);
        await service.sendRequest(makeModel(calls), makeRequest());
        trust.set(false);
        await h.flush(2);
        await assert.rejects(service.sendRequest(makeModel(calls), makeRequest()));

        assert.strictEqual(calls.length, 1, 'only the trusted request reaches the provider');
    });

    it('ignores workspace request settings while untrusted', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        preferences.scopes[PREFERENCE_NAME_REQUEST_SETTINGS] = {
            defaultValue: [],
            globalValue: [{ scope: { providerId: 'anthropic' }, requestSettings: { temperature: 0.2 } }],
            workspaceValue: [{ scope: { providerId: 'anthropic' }, requestSettings: { temperature: 1.5 } }]
        };
        preferences.scopes[PREFERENCE_NAME_THINKING_MODE] = {
            defaultValue: [],
            workspaceValue: [{ scope: { providerId: 'anthropic' }, thinkingMode: { enabled: true } }]
        };
        const service = buildService(preferences, trust);
        const calls = [];

        await assert.rejects(service.sendRequest(makeModel(calls), makeRequest()));
        assert.strictEqual(calls.length, 0);
    });
});
