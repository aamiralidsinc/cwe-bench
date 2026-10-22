'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { AIActivationService } = require('@theia/ai-core/lib/browser/ai-activation-service');
const { AICommandHandlerFactory } = require('@theia/ai-core/lib/browser/ai-command-handler-factory');
const { AiCoreCommandContribution, AI_SHOW_MODEL_STATUS_COMMAND } = require('@theia/ai-core/lib/browser/ai-core-command-contribution');
const { PREFERENCE_NAME_ENABLE_AI } = require('@theia/ai-ide/lib/common/ai-ide-preferences');

function buildActivationContainer(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    container.load(h.loadModule('@theia/ai-chat/lib/browser/ai-chat-frontend-module'));
    container.load(h.loadModule('@theia/ai-ide/lib/browser/frontend-module'));
    h.bindInfrastructure(container, {
        preferences,
        trust,
        contextKeys: h.makeContextKeyService()
    });
    return container;
}

async function start(container) {
    const activation = container.get(AIActivationService);
    await activation.initialize();
    await h.flush(4);
    return activation;
}

describe('AI command availability', () => {
    it('is enabled and visible in a trusted workspace with AI enabled', async () => {
        const preferences = h.makePreferenceService();
        preferences.effective[PREFERENCE_NAME_ENABLE_AI] = true;
        const container = buildActivationContainer(preferences, h.makeTrust(true));
        await start(container);

        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => undefined });
        assert.strictEqual(wrapped.isVisible(), true);
        assert.strictEqual(wrapped.isEnabled(), true);
    });

    it('keeps AI commands visible in an untrusted workspace when AI is enabled', async () => {
        const preferences = h.makePreferenceService();
        preferences.effective[PREFERENCE_NAME_ENABLE_AI] = true;
        const container = buildActivationContainer(preferences, h.makeTrust(false));
        await start(container);

        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => undefined });
        assert.strictEqual(wrapped.isVisible(), true);
    });

    it('hides AI commands when AI is disabled in the preferences', async () => {
        const preferences = h.makePreferenceService();
        preferences.effective[PREFERENCE_NAME_ENABLE_AI] = false;
        const container = buildActivationContainer(preferences, h.makeTrust(true));
        await start(container);

        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => undefined });
        assert.strictEqual(wrapped.isVisible(), false);
        assert.strictEqual(wrapped.isEnabled(), false);
    });

    it('executes again after trust is granted at runtime', async () => {
        const preferences = h.makePreferenceService();
        preferences.effective[PREFERENCE_NAME_ENABLE_AI] = true;
        const trust = h.makeTrust(false);
        const container = buildActivationContainer(preferences, trust);
        await start(container);

        trust.set(true);
        await h.flush(3);

        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => undefined });
        assert.strictEqual(wrapped.isVisible(), true);
        assert.strictEqual(wrapped.isEnabled(), true);
    });

    it('runs every command of the AI core contribution while execution is allowed', async () => {
        const preferences = h.makePreferenceService();
        const container = h.newContainer();
        container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
        h.bindInfrastructure(container, { preferences });
        h.bind(container, AIActivationService, {
            isActive: true,
            canRun: true,
            onDidChangeActiveStatus: () => h.disposable(),
            onDidChangeCanRun: () => h.disposable()
        });
        const registry = h.makeRegistry();
        container.get(AiCoreCommandContribution).registerCommands(registry);

        assert.ok(
            registry.commands.has(AI_SHOW_MODEL_STATUS_COMMAND.id),
            'the model status command must still be registered'
        );
        const handlers = Array.from(registry.commands.values());
        assert.ok(handlers.length > 0);
        for (const handler of handlers) {
            assert.strictEqual(handler.isEnabled(), true);
            await handler.execute();
        }
    });
});
