'use strict';

const assert = require('assert');
const h = require('../support/harness');
const URI = require('@theia/core/lib/common/uri').default;

const { TemplatePreferenceContribution } = require('@theia/ai-ide/lib/browser/template-preference-contribution');
const {
    DefaultPromptFragmentCustomizationService
} = require('@theia/ai-core/lib/browser/frontend-prompt-customization-service');
const { WorkspaceService } = require('@theia/workspace/lib/browser');
const {
    PROMPT_TEMPLATE_WORKSPACE_DIRECTORIES_PREF,
    PROMPT_TEMPLATE_ADDITIONAL_EXTENSIONS_PREF,
    PROMPT_TEMPLATE_WORKSPACE_FILES_PREF
} = require('@theia/ai-ide/lib/common/workspace-preferences');

function buildContribution(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    container.load(h.loadModule('@theia/ai-chat/lib/browser/ai-chat-frontend-module'));
    container.load(h.loadModule('@theia/ai-ide/lib/browser/frontend-module'));
    const customization = {
        calls: [],
        async updateConfiguration(properties) {
            customization.calls.push(JSON.parse(JSON.stringify(properties)));
        }
    };
    h.bind(container, DefaultPromptFragmentCustomizationService, customization);
    h.bindInfrastructure(container, { preferences, trust });
    h.bind(container, WorkspaceService, {
        ready: Promise.resolve(),
        tryGetRoots: () => [{ resource: URI.fromFilePath('/workspace') }],
        onWorkspaceLocationChanged: () => h.disposable(),
        onWorkspaceChanged: () => h.disposable()
    });
    container.bind(TemplatePreferenceContribution).toSelf().inSingletonScope();
    return { contribution: container.get(TemplatePreferenceContribution), customization };
}

function workspaceTemplatePreferences(preferences) {
    preferences.scopes[PROMPT_TEMPLATE_WORKSPACE_DIRECTORIES_PREF] = {
        defaultValue: ['.prompts'],
        workspaceValue: ['.evil/prompts']
    };
    preferences.scopes[PROMPT_TEMPLATE_ADDITIONAL_EXTENSIONS_PREF] = {
        defaultValue: [],
        workspaceValue: ['.evil-extension']
    };
    preferences.scopes[PROMPT_TEMPLATE_WORKSPACE_FILES_PREF] = {
        defaultValue: [],
        workspaceValue: ['.evil/prompts/pwn.prompttemplate']
    };
}

describe('workspace prompt templates in an untrusted workspace', () => {
    it('do not contribute any workspace path or extension', async () => {
        const preferences = h.makePreferenceService();
        workspaceTemplatePreferences(preferences);
        const trust = h.makeTrust(false);
        const { contribution, customization } = buildContribution(preferences, trust);

        contribution.onStart();
        await h.flush(8);

        assert.ok(customization.calls.length > 0, 'the template configuration is still updated');
        for (const properties of customization.calls) {
            for (const path of properties.directoryPaths || []) {
                assert.ok(!String(path).startsWith('/workspace'), `workspace directory leaked: ${path}`);
            }
            for (const path of properties.filePaths || []) {
                assert.ok(!String(path).startsWith('/workspace'), `workspace file leaked: ${path}`);
            }
            for (const extension of properties.extensions || []) {
                assert.notStrictEqual(extension, '.evil-extension', 'workspace extension leaked');
            }
        }
    });

    it('do not use a built-in default that names a location inside the workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[PROMPT_TEMPLATE_WORKSPACE_DIRECTORIES_PREF] = {
            defaultValue: ['.prompts']
        };
        const trust = h.makeTrust(false);
        const { contribution, customization } = buildContribution(preferences, trust);

        contribution.onStart();
        await h.flush(8);

        assert.ok(customization.calls.length > 0, 'the template configuration is still updated');
        for (const properties of customization.calls) {
            for (const path of properties.directoryPaths || []) {
                assert.ok(!String(path).startsWith('/workspace'), `default workspace directory leaked: ${path}`);
            }
        }
    });

    it('reload when workspace trust changes at runtime', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[PROMPT_TEMPLATE_WORKSPACE_DIRECTORIES_PREF] = {
            defaultValue: [],
            workspaceValue: ['.team/prompts']
        };
        const trust = h.makeTrust(false);
        const { contribution, customization } = buildContribution(preferences, trust);

        contribution.onStart();
        await h.flush(8);
        for (const properties of customization.calls) {
            for (const path of properties.directoryPaths || []) {
                assert.ok(!String(path).startsWith('/workspace'), `workspace directory leaked while untrusted: ${path}`);
            }
        }

        trust.set(true);
        await h.flush(8);
        const trusted = customization.calls[customization.calls.length - 1];
        assert.deepStrictEqual(trusted.directoryPaths, ['/workspace/.team/prompts']);

        trust.set(false);
        await h.flush(8);
        const untrusted = customization.calls[customization.calls.length - 1];
        for (const path of untrusted.directoryPaths || []) {
            assert.ok(!String(path).startsWith('/workspace'), `workspace directory leaked after trust loss: ${path}`);
        }
    });
});
