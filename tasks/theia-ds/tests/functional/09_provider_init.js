'use strict';

const assert = require('assert');
const h = require('../support/harness');

const {
    CopilotFrontendApplicationContribution
} = require('@theia/ai-copilot/lib/browser/copilot-frontend-application-contribution');
const {
    CopilotLanguageModelsManager,
    CopilotAuthService
} = require('@theia/ai-copilot/lib/common');
const {
    COPILOT_ENABLED_PREF,
    COPILOT_MODEL_OVERRIDES_PREF
} = require('@theia/ai-copilot/lib/common/copilot-preferences');
const { AICorePreferences } = require('@theia/ai-core/lib/common/ai-core-preferences');
const { AIActivationService } = require('@theia/ai-core/lib/browser/ai-activation-service');
const { MessageService } = require('@theia/core/lib/common/message-service');
const { CommandService } = require('@theia/core/lib/common/command');

function buildContribution(preferences, activation) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-copilot/lib/browser/copilot-frontend-module'));
    const manager = {
        created: [],
        setEnterpriseUrl() { /* no-op */ },
        createOrUpdateLanguageModels(...models) {
            manager.created.push(...models);
        },
        removeLanguageModels() { /* no-op */ },
        fetchAvailableModelIds: async () => [],
        refreshModelsStatus() { /* no-op */ }
    };
    const auth = {
        getAuthState: async () => ({ isAuthenticated: false }),
        onAuthStateChanged: () => h.disposable()
    };
    h.bind(container, CopilotLanguageModelsManager, manager);
    h.bind(container, CopilotAuthService, auth);
    h.bind(container, AICorePreferences, {
        get: () => 3,
        onPreferenceChanged: () => h.disposable()
    });
    h.bind(container, MessageService, {
        info: async () => undefined,
        warn: async () => undefined,
        error: async () => undefined
    });
    h.bind(container, CommandService, { executeCommand: async () => undefined });
    h.bindInfrastructure(container, { preferences });
    h.bind(container, AIActivationService, activation);
    return { contribution: container.get(CopilotFrontendApplicationContribution), manager };
}

describe('provider initialisation', () => {
    it('registers configured models while execution is allowed', async () => {
        const preferences = h.makePreferenceService();
        preferences.effective[COPILOT_ENABLED_PREF] = true;
        preferences.effective[COPILOT_MODEL_OVERRIDES_PREF] = ['gpt-test'];
        const activation = {
            isActive: true,
            canRun: true,
            onDidChangeActiveStatus: () => h.disposable(),
            onDidChangeCanRun: () => h.disposable()
        };
        const { contribution, manager } = buildContribution(preferences, activation);

        contribution.onStart();
        await h.flush(8);

        const ids = manager.created.map(model => model.id);
        assert.ok(ids.includes('copilot/gpt-test'), `registered: ${ids.join(',')}`);
    });
});
