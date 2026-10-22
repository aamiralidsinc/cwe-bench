'use strict';

/**
 * Shared fixtures for the hidden tests.
 *
 * Everything here is test-side bookkeeping: preferences, workspace trust, a
 * command registry and a few proxies. Expected values are computed in the
 * tests themselves and never by the product code under test.
 */

const { Container } = require('@theia/core/shared/inversify');

function disposable(fn) {
    return { dispose: fn || (() => undefined) };
}

function flush(rounds) {
    let chain = Promise.resolve();
    for (let i = 0; i < (rounds || 10); i++) {
        chain = chain.then(() => new Promise(resolve => setImmediate(resolve)));
    }
    return chain;
}

/**
 * PreferenceService stub with the four scopes the code can inspect.
 * `scopes[name] = { defaultValue, globalValue, workspaceValue, workspaceFolderValue }`
 * `effective[name]` (optional) overrides the merged value returned by get().
 */
function makePreferenceService() {
    const service = {
        scopes: Object.create(null),
        effective: Object.create(null),
        updates: [],
        listeners: [],
        ready: Promise.resolve(),
        get(name, fallback) {
            if (Object.prototype.hasOwnProperty.call(service.effective, name)) {
                return service.effective[name];
            }
            const scope = service.scopes[name];
            if (!scope) {
                return fallback;
            }
            const ordered = ['workspaceFolderValue', 'workspaceValue', 'globalValue', 'defaultValue'];
            for (const key of ordered) {
                if (Object.prototype.hasOwnProperty.call(scope, key) && scope[key] !== undefined) {
                    return scope[key];
                }
            }
            return fallback;
        },
        inspect(name) {
            return service.scopes[name];
        },
        set(name, value) {
            service.updates.push({ name, value });
            service.effective[name] = value;
        },
        updateValue(name, value) {
            service.updates.push({ name, value });
            service.effective[name] = value;
            return Promise.resolve();
        },
        onPreferenceChanged(listener) {
            service.listeners.push(listener);
            return disposable();
        },
        onPreferencesChanged(listener) {
            service.listeners.push(listener);
            return disposable();
        },
        overriddenPreferenceName() {
            return undefined;
        },
        getConfigUri() {
            return undefined;
        }
    };
    return service;
}

/**
 * WorkspaceTrustService stub. Until `resolve` is called, getWorkspaceTrust()
 * stays pending, which is how the tests exercise the fail-closed start-up.
 */
function makeTrust(initial) {
    const listeners = new Set();
    let current;
    let resolvePending;
    const pending = new Promise(resolve => {
        resolvePending = resolve;
    });
    const trust = {
        getWorkspaceTrust() {
            if (current !== undefined) {
                return Promise.resolve(current);
            }
            return pending;
        },
        onDidChangeWorkspaceTrust(listener) {
            listeners.add(listener);
            return disposable(() => listeners.delete(listener));
        },
        isWorkspaceTrustResolved() {
            return current !== undefined;
        },
        async setWorkspaceTrust(value) {
            current = value;
            listeners.forEach(listener => listener(value));
        },
        resolve(value) {
            current = value;
            resolvePending(value);
        },
        set(value) {
            current = value;
            listeners.forEach(listener => listener(value));
        },
        get resolved() {
            return current !== undefined;
        },
        get value() {
            return current;
        }
    };
    if (initial !== undefined) {
        trust.resolve(initial);
    }
    return trust;
}

function makeContextKeyService() {
    return {
        createKey(_name, defaultValue) {
            let value = defaultValue;
            return {
                get: () => value,
                set: next => { value = next; },
                reset: () => { value = undefined; }
            };
        },
        setContext() { /* no-op */ },
        getContext() { return undefined; }
    };
}

function makeLogger() {
    const noop = () => undefined;
    return {
        info: noop, warn: noop, error: noop, debug: noop, trace: noop,
        fatal: noop, log: noop,
        setLogLevel: noop,
        getLogLevel: () => 'info',
        isEnabled: () => true,
        ifEnabled: noop,
        child: () => makeLogger()
    };
}

function makeRegistry() {
    const commands = new Map();
    return {
        commands,
        registerCommand(command, handler) {
            commands.set(typeof command === 'string' ? command : command.id, handler);
            return disposable();
        },
        executeCommand() {
            return Promise.resolve(undefined);
        },
        getCommand(id) {
            return commands.get(id);
        }
    };
}

function newContainer() {
    return new Container({ skipBaseClassChecks: true });
}

function bind(container, identifier, value) {
    if (container.isBound(identifier)) {
        container.rebind(identifier).toConstantValue(value);
    } else {
        container.bind(identifier).toConstantValue(value);
    }
}

/**
 * Binds the infrastructure every product service in these tests needs.
 */
function bindInfrastructure(container, options) {
    const opts = options || {};
    const logger = opts.logger || makeLogger();
    if (opts.preferences) {
        bind(container, require('@theia/core/lib/common/preferences').PreferenceService, opts.preferences);
    }
    if (opts.trust) {
        bind(container, require('@theia/workspace/lib/browser/workspace-trust-service').WorkspaceTrustService, opts.trust);
    }
    if (opts.contextKeys) {
        bind(container, require('@theia/core/lib/browser/context-key-service').ContextKeyService, opts.contextKeys);
    }
    if (!opts.skipPlainLogger) {
        bind(container, require('@theia/core/lib/common/logger').ILogger, logger);
    }
    for (const name of opts.namedLoggers || []) {
        container.bind(require('@theia/core/lib/common/logger').ILogger)
            .toConstantValue(logger)
            .whenTargetNamed(name);
    }
    return { logger };
}

function loadModule(modulePath) {
    const loaded = require(modulePath);
    return loaded && loaded.default ? loaded.default : loaded;
}

module.exports = {
    bind,
    bindInfrastructure,
    disposable,
    flush,
    loadModule,
    makeContextKeyService,
    makeLogger,
    makePreferenceService,
    makeRegistry,
    makeTrust,
    newContainer
};
