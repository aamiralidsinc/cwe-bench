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

describe('workspace prompt templates', () => {
    it('are loaded in a trusted workspace', async () => {
        const preferences = h.makePreferenceService();
        preferences.scopes[PROMPT_TEMPLATE_WORKSPACE_DIRECTORIES_PREF] = {
            defaultValue: ['.prompts'],
            workspaceValue: ['.team/prompts']
        };
        preferences.scopes[PROMPT_TEMPLATE_ADDITIONAL_EXTENSIONS_PREF] = {
            defaultValue: [],
            workspaceValue: ['.team-extension']
        };
        preferences.scopes[PROMPT_TEMPLATE_WORKSPACE_FILES_PREF] = {
            defaultValue: [],
            workspaceValue: ['.team/prompts/extra.prompttemplate']
        };
        const { contribution, customization } = buildContribution(preferences, h.makeTrust(true));

        contribution.onStart();
        await h.flush(8);

        assert.ok(customization.calls.length > 0);
        const last = customization.calls[customization.calls.length - 1];
        assert.deepStrictEqual(last.directoryPaths, ['/workspace/.team/prompts']);
        assert.deepStrictEqual(last.filePaths, ['/workspace/.team/prompts/extra.prompttemplate']);
        assert.deepStrictEqual(last.extensions, ['.team-extension']);
    });
});
