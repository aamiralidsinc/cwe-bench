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

describe('tool approval in an untrusted workspace', () => {
    it('ignores a workspace wildcard that would auto-approve every tool', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: { '*': ToolConfirmationMode.CONFIRM },
            workspaceValue: { '*': ToolConfirmationMode.ALWAYS_ALLOW }
        };
        const trust = h.makeTrust(false);
        const manager = await prepare(preferences, trust);

        assert.strictEqual(
            manager.getConfirmationMode('some-tool', 'chat-1'),
            ToolConfirmationMode.CONFIRM,
            'the workspace wildcard must not be honored'
        );
    });

    it('ignores a workspace per-tool auto-approval for a tool that always needs confirmation', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: {},
            workspaceValue: { 'dangerous-tool': ToolConfirmationMode.ALWAYS_ALLOW }
        };
        const trust = h.makeTrust(false);
        const manager = await prepare(preferences, trust);

        assert.strictEqual(
            manager.getConfirmationMode('dangerous-tool', 'chat-1', { id: 'dangerous-tool', confirmAlwaysAllow: true }),
            ToolConfirmationMode.CONFIRM
        );
    });

    it('ignores a folder-scoped approval override', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[TOOL_CONFIRMATION_PREFERENCE] = {
            defaultValue: { '*': ToolConfirmationMode.CONFIRM },
            workspaceFolderValue: { '*': ToolConfirmationMode.ALWAYS_ALLOW }
        };
        const trust = h.makeTrust(false);
        const manager = await prepare(preferences, trust);

        assert.strictEqual(
            manager.getConfirmationMode('some-tool', 'chat-1'),
            ToolConfirmationMode.CONFIRM
        );
    });
});
