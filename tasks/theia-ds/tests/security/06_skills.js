'use strict';

const assert = require('assert');
const h = require('../support/harness');
const URI = require('@theia/core/lib/common/uri').default;

const { SkillService } = require('@theia/ai-core/lib/browser/skill-service');
const { AICorePreferences, PREFERENCE_NAME_SKILL_DIRECTORIES } = require('@theia/ai-core/lib/common/ai-core-preferences');
const { FileService } = require('@theia/filesystem/lib/browser/file-service');
const { EnvVariablesServer } = require('@theia/core/lib/common/env-variables');
const { WorkspaceService } = require('@theia/workspace/lib/browser');

const DIRECTORIES = {
    '/workspace': [],
    '/workspace/.prompts/skills': ['workspace-skill'],
    '/home/user': [],
    '/home/user/.config': [],
    '/home/user/.config/skills': ['user-skill'],
    '/tmp/user-skills': ['user-cli-skill'],
    '/tmp/evil-skills': ['evil-cli-skill']
};

function skillContent(name) {
    return `---\nname: ${name}\ndescription: Skill named ${name}\n---\nbody of ${name}\n`;
}

function makeFileService() {
    return {
        exists: async uri => {
            const path = uri.path.fsPath();
            if (path.endsWith('/SKILL.md')) {
                return true;
            }
            return Object.prototype.hasOwnProperty.call(DIRECTORIES, path);
        },
        resolve: async uri => {
            const path = uri.path.fsPath();
            const children = DIRECTORIES[path];
            if (!children) {
                return { children: undefined };
            }
            return {
                children: children.map(name => ({
                    isDirectory: true,
                    name,
                    resource: URI.fromFilePath(`${path}/${name}`)
                }))
            };
        },
        read: async uri => {
            const path = uri.path.fsPath();
            const name = path.split('/').slice(-2)[0];
            return { value: skillContent(name) };
        },
        watch: () => h.disposable(),
        onDidFilesChange: () => h.disposable()
    };
}

function makeCorePreferences(preferences) {
    const proxy = {
        onPreferenceChanged: () => h.disposable()
    };
    Object.defineProperty(proxy, PREFERENCE_NAME_SKILL_DIRECTORIES, {
        get: () => preferences.get(PREFERENCE_NAME_SKILL_DIRECTORIES, [])
    });
    return proxy;
}

function buildService(preferences, trust) {
    const container = h.newContainer();
    container.load(h.loadModule('@theia/ai-core/lib/browser/ai-core-frontend-module'));
    h.bind(container, AICorePreferences, makeCorePreferences(preferences));
    h.bind(container, FileService, makeFileService());
    h.bind(container, EnvVariablesServer, {
        getHomeDirUri: async () => URI.fromFilePath('/home/user').toString(),
        getConfigDirUri: async () => URI.fromFilePath('/home/user/.config').toString()
    });
    h.bind(container, WorkspaceService, {
        ready: Promise.resolve(),
        tryGetRoots: () => [{ resource: URI.fromFilePath('/workspace') }],
        onWorkspaceChanged: () => h.disposable()
    });
    h.bindInfrastructure(container, { preferences, trust, namedLoggers: ['SkillService'], skipPlainLogger: true });
    return container.getAsync(SkillService);
}

function setSkillDirectories(preferences) {
    preferences.scopes[PREFERENCE_NAME_SKILL_DIRECTORIES] = {
        defaultValue: [],
        globalValue: ['/tmp/user-skills'],
        workspaceValue: ['/tmp/evil-skills']
    };
}

describe('skills in an untrusted workspace', () => {
    it('are not loaded from the workspace prompts directory', async () => {
        const preferences = h.makePreferenceService();
        setSkillDirectories(preferences);
        const trust = h.makeTrust(false);
        const service = await buildService(preferences, trust);
        await service.ready;

        const names = service.getSkills().map(skill => skill.name);
        assert.ok(!names.includes('workspace-skill'), `workspace skill loaded: ${names.join(',')}`);
    });

    it('are not loaded from workspace-scoped extra directories', async () => {
        const preferences = h.makePreferenceService();
        setSkillDirectories(preferences);
        const trust = h.makeTrust(false);
        const service = await buildService(preferences, trust);
        await service.ready;

        const names = service.getSkills().map(skill => skill.name);
        assert.ok(!names.includes('evil-cli-skill'), `workspace configured skill loaded: ${names.join(',')}`);
    });
});
