'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { AISettingsService } = require('@theia/ai-core/lib/common/settings-service');
const { LanguageModelAliasRegistry } = require('@theia/ai-core/lib/common/language-model-alias');
const { LANGUAGE_MODEL_ALIASES_PREFERENCE } = require('@theia/ai-core/lib/common/ai-core-preferences');

const AGENT_SETTINGS = 'ai-features.agentSettings';

async function prepare(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    h.bindInfrastructure(container, { preferences, trust });
    const settings = container.get(AISettingsService);
    const aliases = container.get(LanguageModelAliasRegistry);
    await h.flush(3);
    await aliases.ready;
    return { settings, aliases };
}

describe('AI settings readers', () => {
    it('apply workspace agent settings in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            globalValue: { 'the-agent': { temperature: 0.1 } },
            workspaceValue: { 'the-agent': { temperature: 0.9 } }
        };
        const { settings } = await prepare(preferences, h.makeTrust(true));

        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.9 } });
    });

    it('apply user-level agent settings in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            globalValue: { 'the-agent': { temperature: 0.1 } }
        };
        const { settings } = await prepare(preferences, h.makeTrust(false));

        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.1 } });
    });

    it('fall back to the built-in default settings', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = { defaultValue: {} };
        const { settings } = await prepare(preferences, h.makeTrust(false));

        assert.deepStrictEqual(await settings.getSettings(), {});
    });

    it('re-read user-level agent settings when the preference changes while untrusted', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            globalValue: { 'the-agent': { temperature: 0.1 } }
        };
        const { settings } = await prepare(preferences, h.makeTrust(false));
        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.1 } });

        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            globalValue: { 'the-agent': { temperature: 0.3 } }
        };
        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.3 } });
    });

    it('apply workspace alias selections in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[LANGUAGE_MODEL_ALIASES_PREFERENCE] = {
            defaultValue: {},
            globalValue: { 'default/universal': { selectedModel: 'global/model' } },
            workspaceValue: { 'default/universal': { selectedModel: 'workspace/model' } }
        };
        const { aliases } = await prepare(preferences, h.makeTrust(true));

        assert.deepStrictEqual(aliases.resolveAlias('default/universal'), ['workspace/model']);
    });

    it('apply user-level alias selections in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[LANGUAGE_MODEL_ALIASES_PREFERENCE] = {
            defaultValue: {},
            globalValue: { 'default/universal': { selectedModel: 'global/model' } }
        };
        const { aliases } = await prepare(preferences, h.makeTrust(false));

        assert.deepStrictEqual(aliases.resolveAlias('default/universal'), ['global/model']);
    });

    it('fall back to the alias default models', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[LANGUAGE_MODEL_ALIASES_PREFERENCE] = { defaultValue: {} };
        const { aliases } = await prepare(preferences, h.makeTrust(false));

        const resolved = aliases.resolveAlias('default/universal');
        assert.ok(Array.isArray(resolved) && resolved.length > 0);
        assert.notStrictEqual(resolved[0], 'global/model');
    });
});
