'use strict';

const assert = require('assert');
const h = require('../support/harness');

const { ShellCommandPermissionService } = require('@theia/ai-terminal/lib/browser/shell-command-permission-service');
const { ShellCommandAnalyzer } = require('@theia/ai-terminal/lib/common/shell-command-analyzer');
const {
    SHELL_COMMAND_ALLOWLIST_PREFERENCE,
    SHELL_COMMAND_DENYLIST_PREFERENCE
} = require('@theia/ai-terminal/lib/common/shell-command-preferences');

function makeAnalyzer() {
    return {
        parseCommand: command => [command],
        containsDangerousPatterns: command => /[$`]/.test(command)
    };
}

function buildService(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    container.load(h.loadModule('@theia/ai-terminal/lib/browser/ai-terminal-frontend-module'));
    h.bindInfrastructure(container, { preferences, trust });
    h.bind(container, ShellCommandAnalyzer, makeAnalyzer());
    return container.get(ShellCommandPermissionService);
}

describe('shell command approval settings', () => {
    it('apply workspace allowlist entries in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = {
            defaultValue: [],
            workspaceValue: ['git status']
        };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = { defaultValue: ['sudo *'] };
        const service = buildService(preferences, h.makeTrust(true));
        await h.flush(2);

        assert.strictEqual(service.isCommandAllowed('git status'), true);
    });

    it('apply user-level allowlist entries in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = {
            defaultValue: [],
            globalValue: ['git status']
        };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = { defaultValue: ['sudo *'] };
        const service = buildService(preferences, h.makeTrust(false));
        await h.flush(2);

        assert.strictEqual(service.isCommandAllowed('git status'), true);
    });

    it('keep the built-in deny list in an untrusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = {
            defaultValue: [],
            globalValue: ['sudo *']
        };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = { defaultValue: ['sudo *'] };
        const service = buildService(preferences, h.makeTrust(false));
        await h.flush(2);

        assert.strictEqual(service.isCommandAllowed('sudo ls'), false);
    });

    it('do not approve commands without an allowlist entry', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = { defaultValue: [] };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = { defaultValue: ['sudo *'] };
        const service = buildService(preferences, h.makeTrust(false));
        await h.flush(2);

        assert.strictEqual(service.isCommandAllowed('git status'), false);
    });
});
