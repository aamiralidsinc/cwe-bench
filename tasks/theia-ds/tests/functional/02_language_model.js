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

describe('language model requests', () => {
    it('are sent in a trusted workspace and merge workspace request settings', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[PREFERENCE_NAME_REQUEST_SETTINGS] = {
            defaultValue: [],
            globalValue: [{ scope: { providerId: 'anthropic' }, requestSettings: { temperature: 0.2 } }],
            workspaceValue: [{ scope: { providerId: 'anthropic' }, requestSettings: { temperature: 1.5 } }]
        };
        preferences.scopes[PREFERENCE_NAME_THINKING_MODE] = {
            defaultValue: [],
            workspaceValue: [{ scope: { providerId: 'anthropic' }, thinkingMode: { enabled: true } }]
        };
        const service = buildService(preferences, h.makeTrust(true));
        const calls = [];

        const response = await service.sendRequest(makeModel(calls), makeRequest());

        assert.deepStrictEqual(response, { type: 'text', text: 'ok' });
        assert.strictEqual(calls.length, 1);
        assert.strictEqual(calls[0].settings.temperature, 1.5);
        assert.deepStrictEqual(calls[0].thinkingMode, { enabled: true });
        assert.strictEqual(service.sessions.length, 1);
    });

    it('merge user-level request settings in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[PREFERENCE_NAME_REQUEST_SETTINGS] = {
            defaultValue: [],
            globalValue: [{ scope: { providerId: 'anthropic' }, requestSettings: { temperature: 0.2 } }]
        };
        const service = buildService(preferences, h.makeTrust(true));
        const calls = [];

        await service.sendRequest(makeModel(calls), makeRequest());

        assert.strictEqual(calls[0].settings.temperature, 0.2);
    });

    it('work after trust is granted at runtime', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const service = buildService(preferences, trust);
        const calls = [];

        trust.set(true);
        await h.flush(3);
        await service.sendRequest(makeModel(calls), makeRequest());

        assert.strictEqual(calls.length, 1);
    });
});
