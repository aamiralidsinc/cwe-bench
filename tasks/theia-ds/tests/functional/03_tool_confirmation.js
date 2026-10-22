'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { ToolConfirmationManager } = require('@theia/ai-chat/lib/browser/chat-tool-preference-bindings');
const {
    ToolConfirmationMode,
    TOOL_CONFIRMATION_PREFERENCE
} = require('@theia/ai-chat/lib/common/chat-tool-preferences');

function buildManager(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    container.load(h.loadModule('@theia/ai-chat/lib/browser/ai-chat-frontend-module'));
    h.bindInfrastructure(container, { preferences, trust });
    return container.get(ToolConfirmationManager);
}

async function prepare(preferences, trust) {
    const manager = buildManager(preferences, trust);
    await h.flush(3);
    return manager;
}

describe('tool approval settings', () => {
    it('apply workspace wildcard overrides in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: { '*': ToolConfirmationMode.CONFIRM },
            workspaceValue: { '*': ToolConfirmationMode.ALWAYS_ALLOW }
        };
        const manager = await prepare(preferences, h.makeTrust(true));

        assert.strictEqual(manager.getConfirmationMode('some-tool', 'chat-1'), ToolConfirmationMode.ALWAYS_ALLOW);
    });

    it('apply user-level wildcard overrides in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: { '*': ToolConfirmationMode.CONFIRM },
            globalValue: { '*': ToolConfirmationMode.ALWAYS_ALLOW }
        };
        const manager = await prepare(preferences, h.makeTrust(false));

        assert.strictEqual(manager.getConfirmationMode('some-tool', 'chat-1'), ToolConfirmationMode.ALWAYS_ALLOW);
    });

    it('apply the built-in default in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: { '*': ToolConfirmationMode.CONFIRM }
        };
        const manager = await prepare(preferences, h.makeTrust(false));

        assert.strictEqual(manager.getConfirmationMode('some-tool', 'chat-1'), ToolConfirmationMode.CONFIRM);
    });

    it('let a session-only override win in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: { '*': ToolConfirmationMode.ALWAYS_ALLOW }
        };
        const manager = await prepare(preferences, h.makeTrust(false));

        manager.setSessionConfirmationMode('some-tool', ToolConfirmationMode.DISABLED, 'chat-1');
        assert.strictEqual(manager.getConfirmationMode('some-tool', 'chat-1'), ToolConfirmationMode.DISABLED);
    });

    it('still persist a user choice made in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = { defaultValue: {} };
        const manager = await prepare(preferences, h.makeTrust(false));

        manager.setConfirmationMode('some-tool', ToolConfirmationMode.CONFIRM);

        assert.strictEqual(preferences.updates.length, 1);
        assert.strictEqual(preferences.updates[0].name, TOOL_CONFIRMATION_PREFERENCE);
        assert.strictEqual(preferences.updates[0].value['some-tool'], ToolConfirmationMode.CONFIRM);
    });

    it('apply workspace per-tool overrides in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: {},
            workspaceValue: { 'some-tool': ToolConfirmationMode.DISABLED }
        };
        const manager = await prepare(preferences, h.makeTrust(true));

        assert.strictEqual(manager.getConfirmationMode('some-tool', 'chat-1'), ToolConfirmationMode.DISABLED);
    });
});
