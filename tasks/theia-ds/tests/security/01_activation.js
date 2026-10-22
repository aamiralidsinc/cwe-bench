'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { AIActivationService } = require('@theia/ai-core/lib/browser/ai-activation-service');
const { AICommandHandlerFactory } = require('@theia/ai-core/lib/browser/ai-command-handler-factory');
const { AiCoreCommandContribution } = require('@theia/ai-core/lib/browser/ai-core-command-contribution');
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
    preferences.effective[PREFERENCE_NAME_ENABLE_AI] = true;
    return container;
}

describe('AI execution is gated on workspace trust', () => {
    it('does not allow execution in an untrusted workspace although AI is enabled', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const container = buildActivationContainer(preferences, trust);
        const activation = container.get(AIActivationService);

        await activation.initialize();
        await h.flush(4);

        assert.strictEqual(activation.isActive, true, 'AI stays enabled in preferences');
        assert.strictEqual(activation.canRun, false, 'execution must be refused in an untrusted workspace');
    });

    it('keeps command visibility but disables command execution in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const container = buildActivationContainer(preferences, trust);
        const activation = container.get(AIActivationService);
        await activation.initialize();
        await h.flush(4);

        const factory = container.get(AICommandHandlerFactory);
        const wrapped = factory({ execute: () => undefined });

        assert.strictEqual(wrapped.isVisible(), true, 'the command stays visible');
        assert.strictEqual(wrapped.isEnabled(), false, 'the command must not be executable');
    });

    it('refuses programmatic command execution in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const container = buildActivationContainer(preferences, trust);
        const activation = container.get(AIActivationService);
        await activation.initialize();
        await h.flush(4);

        let executed = false;
        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => { executed = true; } });
        assert.strictEqual(wrapped.isEnabled(), false);
        await assert.rejects(async () => wrapped.execute(), 'execution must be refused, not only hidden in the UI');
        assert.strictEqual(executed, false, 'the handler must not run');
    });

    it('fails closed while the trust state has not been resolved', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust();
        const container = buildActivationContainer(preferences, trust);
        const activation = container.get(AIActivationService);

        await activation.initialize();
        await h.flush(4);

        assert.strictEqual(activation.isActive, true);
        assert.strictEqual(activation.canRun, false, 'unresolved trust must not allow execution');
        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => undefined });
        assert.strictEqual(wrapped.isEnabled(), false);
    });

    it('re-evaluates execution when workspace trust changes at runtime', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const container = buildActivationContainer(preferences, trust);
        const activation = container.get(AIActivationService);
        await activation.initialize();
        await h.flush(4);
        assert.strictEqual(activation.canRun, false);

        const observed = [];
        activation.onDidChangeCanRun(value => observed.push(value));
        trust.set(true);
        await h.flush(2);

        assert.strictEqual(activation.canRun, true, 'granting trust must allow execution');
        assert.deepStrictEqual(observed, [true]);
        const wrapped = container.get(AICommandHandlerFactory)({ execute: () => undefined });
        assert.strictEqual(wrapped.isEnabled(), true);
    });
});

describe('commands registered directly by the AI core contribution', () => {
    function build(preferences, trust, activation) {
        const container = h.newContainer();
        container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
        h.bindInfrastructure(container, { preferences, trust });
        h.bind(container, AIActivationService, activation);
        return container.get(AiCoreCommandContribution);
    }

    it('are disabled and refuse execution while execution is not allowed', async () => {
        const preferences = h.makePreferenceService();
        const trust = h.makeTrust(false);
        const activation = {
            isActive: true,
            canRun: false,
            onDidChangeActiveStatus: () => h.disposable(),
            onDidChangeCanRun: () => h.disposable()
        };
        const registry = h.makeRegistry();
        build(preferences, trust, activation).registerCommands(registry);

        const handlers = Array.from(registry.commands.values());
        assert.ok(handlers.length > 0, 'the contribution registers commands');
        for (const handler of handlers) {
            assert.strictEqual(handler.isEnabled(), false);
            await assert.rejects(async () => handler.execute(), 'programmatic execution must be refused');
        }
    });
});
