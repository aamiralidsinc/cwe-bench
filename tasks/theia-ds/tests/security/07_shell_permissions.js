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

describe('shell command approval in an untrusted workspace', () => {
    it('ignores a workspace allowlist', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = {
            defaultValue: [],
            workspaceValue: ['git status']
        };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = {
            defaultValue: ['sudo *']
        };
        const trust = h.makeTrust(false);
        const service = buildService(preferences, trust);
        await h.flush(2);

        assert.strictEqual(service.isCommandAllowed('git status'), false);
    });

    it('cannot remove the built-in deny list from workspace settings', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = {
            defaultValue: [],
            workspaceValue: ['sudo *']
        };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = {
            defaultValue: ['sudo *'],
            workspaceValue: []
        };
        const trust = h.makeTrust(false);
        const service = buildService(preferences, trust);
        await h.flush(2);

        const result = service.checkCommand('sudo ls');
        assert.strictEqual(result.allowed, false);
    });

    it('re-evaluates the trust state at runtime', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[SHELL_COMMAND_ALLOWLIST_PREFERENCE] = {
            defaultValue: [],
            workspaceValue: ['git status']
        };
        preferences.scopes[SHELL_COMMAND_DENYLIST_PREFERENCE] = { defaultValue: ['sudo *'] };
        const trust = h.makeTrust(false);
        const service = buildService(preferences, trust);
        await h.flush(2);
        assert.strictEqual(service.isCommandAllowed('git status'), false);

        trust.set(true);
        await h.flush(2);
        assert.strictEqual(service.isCommandAllowed('git status'), true);

        trust.set(false);
        await h.flush(2);
        assert.strictEqual(service.isCommandAllowed('git status'), false);
    });
});
