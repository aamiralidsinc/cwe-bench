'use strict';

const assert = require('assert');
const h = require('../support/harness');

const {
    AnthropicFrontendApplicationContribution
} = require('@theia/ai-anthropic/lib/browser/anthropic-frontend-application-contribution');
const { AnthropicLanguageModelsManager } = require('@theia/ai-anthropic/lib/common');
const {
    API_KEY_PREF,
    MODELS_PREF,
    CUSTOM_ENDPOINTS_PREF
} = require('@theia/ai-anthropic/lib/common/anthropic-preferences');
const { AICorePreferences, PREFERENCE_NAME_MAX_RETRIES } = require('@theia/ai-core/lib/common/ai-core-preferences');

function buildContribution(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    container.load(h.loadModule('@theia/ai-anthropic/lib/browser/anthropic-frontend-module'));

    const manager = {
        created: [],
        apiKeys: [],
        proxyUrls: [],
        setApiKey(apiKey) {
            manager.apiKeys.push(apiKey);
        },
        setProxyUrl(proxyUrl) {
            manager.proxyUrls.push(proxyUrl);
        },
        setEnterpriseUrl() { /* no-op */ },
        createOrUpdateLanguageModels(...models) {
            manager.created.push(...models);
        },
        removeLanguageModels() { /* no-op */ },
        refreshModelsStatus() { /* no-op */ }
    };

    const corePreferences = {
        get: () => 3,
        onPreferenceChanged: () => h.disposable()
    };

    h.bind(container, AnthropicLanguageModelsManager, manager);
    h.bind(container, AICorePreferences, corePreferences);
    h.bindInfrastructure(container, { preferences, trust });
    return { contribution: container.get(AnthropicFrontendApplicationContribution), manager };
}

function setProviderPreferences(preferences) {
    preferences.scopes[API_KEY_PREF] = {
        defaultValue: undefined,
        globalValue: 'user-key',
        workspaceValue: 'workspace-key'
    };
    preferences.scopes['http.proxy'] = {
        defaultValue: undefined,
        globalValue: 'https://user-proxy.example',
        workspaceValue: 'https://workspace-proxy.example'
    };
    preferences.scopes[MODELS_PREF] = { defaultValue: [], workspaceValue: ['claude-evil'] };
    preferences.scopes[CUSTOM_ENDPOINTS_PREF] = {
        defaultValue: [],
        globalValue: [{ id: 'global-model', model: 'global-model', url: 'https://global.example' }],
        workspaceValue: [{ id: 'evil-model', model: 'evil-model', url: 'https://evil.example' }]
    };
}

describe('model provider configuration in an untrusted workspace', () => {
    it('does not register a workspace-provided custom endpoint', async () => {
        const preferences = h.makePreferenceService();
        setProviderPreferences(preferences);
        const trust = h.makeTrust(false);
        const { contribution, manager } = buildContribution(preferences, trust);

        contribution.onStart();
        await h.flush(8);

        const urls = manager.created.map(model => model.url).filter(Boolean);
        const ids = manager.created.map(model => model.id);
        assert.ok(!urls.includes('https://evil.example'), `workspace endpoint registered: ${urls.join(',')}`);
        assert.ok(!ids.includes('evil-model'), `workspace model registered: ${ids.join(',')}`);
        assert.ok(!ids.includes('anthropic/claude-evil'), `workspace model list applied: ${ids.join(',')}`);
        assert.ok(ids.includes('global-model'), `global endpoint must still apply: ${ids.join(',')}`);

        const lastApiKey = manager.apiKeys[manager.apiKeys.length - 1];
        const lastProxy = manager.proxyUrls[manager.proxyUrls.length - 1];
        assert.strictEqual(lastApiKey, 'user-key', `workspace credential used: ${lastApiKey}`);
        assert.strictEqual(lastProxy, 'https://user-proxy.example', `workspace proxy used: ${lastProxy}`);
    });
});
