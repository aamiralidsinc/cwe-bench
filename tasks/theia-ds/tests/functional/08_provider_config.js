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
const { AICorePreferences } = require('@theia/ai-core/lib/common/ai-core-preferences');

function buildContribution(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    container.load(h.loadModule('@theia/ai-anthropic/lib/browser/anthropic-frontend-module'));
    const manager = {
        created: [],
        setApiKey() { /* no-op */ },
        setProxyUrl() { /* no-op */ },
        createOrUpdateLanguageModels(...models) {
            manager.created.push(...models);
        },
        removeLanguageModels() { /* no-op */ },
        refreshModelsStatus() { /* no-op */ }
    };
    h.bind(container, AnthropicLanguageModelsManager, manager);
    h.bind(container, AICorePreferences, {
        get: () => 3,
        onPreferenceChanged: () => h.disposable()
    });
    h.bindInfrastructure(container, { preferences, trust });
    return { contribution: container.get(AnthropicFrontendApplicationContribution), manager };
}

function basePreferences(preferences) {
    preferences.scopes[API_KEY_PREF] = { defaultValue: undefined };
    preferences.scopes[MODELS_PREF] = { defaultValue: [] };
    preferences.scopes[CUSTOM_ENDPOINTS_PREF] = { defaultValue: [] };
}

describe('model provider configuration', () => {
    it('applies workspace endpoints in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        basePreferences(preferences);
        preferences.scopes[CUSTOM_ENDPOINTS_PREF] = {
            defaultValue: [],
            workspaceValue: [{ id: 'team-model', model: 'team-model', url: 'https://team.example' }]
        };
        const { contribution, manager } = buildContribution(preferences, h.makeTrust(true));

        contribution.onStart();
        await h.flush(8);

        const urls = manager.created.map(model => model.url).filter(Boolean);
        assert.ok(urls.includes('https://team.example'), `registered: ${urls.join(',')}`);
    });

    it('applies user-level endpoints in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        basePreferences(preferences);
        preferences.scopes[CUSTOM_ENDPOINTS_PREF] = {
            defaultValue: [],
            globalValue: [{ id: 'user-model', model: 'user-model', url: 'https://user.example' }]
        };
        const { contribution, manager } = buildContribution(preferences, h.makeTrust(false));

        contribution.onStart();
        await h.flush(8);

        const urls = manager.created.map(model => model.url).filter(Boolean);
        assert.ok(urls.includes('https://user.example'), `registered: ${urls.join(',')}`);
    });

    it('keeps the built-in model list when no user or workspace value is set', async () => {
        const preferences = h.makePreferenceService();
        basePreferences(preferences);
        preferences.scopes[MODELS_PREF] = {
            defaultValue: ['claude-default']
        };
        const { contribution, manager } = buildContribution(preferences, h.makeTrust(false));

        contribution.onStart();
        await h.flush(8);

        const ids = manager.created.map(model => model.id);
        assert.ok(ids.includes('anthropic/claude-default'), `registered: ${ids.join(',')}`);
    });
});
