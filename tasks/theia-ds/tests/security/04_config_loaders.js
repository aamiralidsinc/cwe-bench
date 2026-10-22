'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { AISettingsService } = require('@theia/ai-core/lib/common/settings-service');
const { LanguageModelAliasRegistry } = require('@theia/ai-core/lib/common/language-model-alias');
const { LANGUAGE_MODEL_ALIASES_PREFERENCE } = require('@theia/ai-core/lib/common/ai-core-preferences');

const AGENT_SETTINGS = 'ai-features.agentSettings';

function buildContainer(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    h.bindInfrastructure(container, { preferences, trust });
    return container;
}

async function prepare(preferences, trust) {
    const container = buildContainer(preferences, trust);
    const settings = container.get(AISettingsService);
    const aliases = container.get(LanguageModelAliasRegistry);
    await h.flush(3);
    await aliases.ready;
    return { settings, aliases };
}

describe('workspace-scoped AI settings in an untrusted workspace', () => {
    it('are ignored by the agent settings reader', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            globalValue: { 'the-agent': { temperature: 0.1 } },
            workspaceValue: { 'the-agent': { temperature: 2 } }
        };
        const trust = h.makeTrust(false);
        const { settings } = await prepare(preferences, trust);

        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.1 } });
    });

    it('fall back to the built-in default when only a workspace value exists', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            workspaceValue: { 'the-agent': { temperature: 2 } }
        };
        const trust = h.makeTrust(false);
        const { settings } = await prepare(preferences, trust);

        assert.deepStrictEqual(await settings.getSettings(), {});
    });

    it('are ignored by the language model alias registry', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[LANGUAGE_MODEL_ALIASES_PREFERENCE] = {
            defaultValue: {},
            globalValue: { 'default/universal': { selectedModel: 'global/model' } },
            workspaceValue: { 'default/universal': { selectedModel: 'evil/model' } }
        };
        const trust = h.makeTrust(false);
        const { aliases } = await prepare(preferences, trust);

        assert.deepStrictEqual(aliases.resolveAlias('default/universal'), ['global/model']);
    });

    it('re-evaluate the trust state at runtime', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[AGENT_SETTINGS] = {
            defaultValue: {},
            globalValue: { 'the-agent': { temperature: 0.1 } },
            workspaceValue: { 'the-agent': { temperature: 2 } }
        };
        preferences.scopes[LANGUAGE_MODEL_ALIASES_PREFERENCE] = {
            defaultValue: {},
            globalValue: { 'default/universal': { selectedModel: 'global/model' } },
            workspaceValue: { 'default/universal': { selectedModel: 'workspace/model' } }
        };
        const trust = h.makeTrust(false);
        const { settings, aliases } = await prepare(preferences, trust);
        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.1 } });
        assert.deepStrictEqual(aliases.resolveAlias('default/universal'), ['global/model']);

        trust.set(true);
        await h.flush(3);
        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 2 } });
        assert.deepStrictEqual(aliases.resolveAlias('default/universal'), ['workspace/model']);

        trust.set(false);
        await h.flush(3);
        assert.deepStrictEqual(await settings.getSettings(), { 'the-agent': { temperature: 0.1 } });
        assert.deepStrictEqual(aliases.resolveAlias('default/universal'), ['global/model']);
    });
});
