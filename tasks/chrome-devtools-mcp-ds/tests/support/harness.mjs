/**
 * Shared harness for the hidden suites.
 *
 * Everything here talks to the product's own compiled code: a real McpContext,
 * the product's own tool registry and a real ToolHandler, so a test call walks
 * the same path an MCP tool call walks. Only the browser boundary (the object
 * that stands in for Chrome) is provided by the test, because the point under
 * test is which files the server touches, not Chrome itself.
 */
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const PRODUCT = process.env.CDM_PRODUCT_ROOT ?? '/workspace';

const {McpContext} = await import(`${PRODUCT}/build/src/McpContext.js`);
const {Locator} = await import(`${PRODUCT}/build/src/third_party/index.js`);
const {ToolHandler} = await import(`${PRODUCT}/build/src/ToolHandler.js`);
const {Mutex} = await import(`${PRODUCT}/build/src/Mutex.js`);
const {createTools} = await import(`${PRODUCT}/build/src/tools/tools.js`);

const TOOL_ARGS = {
  slim: false,
  categoryExtensions: true,
  experimentalPageIdRouting: false,
  experimentalStructuredContent: false,
  experimentalMemory: true,
  experimentalScreencast: false,
  redactNetworkHeaders: false,
  viaCli: false,
};

function listener() {
  const handlers = {};
  return {
    on(name, fn) {
      (handlers[name] ??= []).push(fn);
    },
    off(name, fn) {
      const list = handlers[name] ?? [];
      const i = list.indexOf(fn);
      if (i >= 0) list.splice(i, 1);
    },
    emit(name, value) {
      for (const fn of [...(handlers[name] ?? [])]) fn(value);
    },
  };
}

/**
 * A directory that is genuinely outside the system temporary area, so "outside
 * the workspace" really is outside the roots that are always allowed.
 */
async function outsideBase() {
  let tmpReal = os.tmpdir();
  try {
    tmpReal = await fs.realpath(os.tmpdir());
  } catch {
    // Keep the lexical value.
  }
  const candidates = [process.env.HOME, os.homedir(), '/var/tmp', '/home'];
  for (const candidate of candidates) {
    if (!candidate) continue;
    let real;
    try {
      real = await fs.realpath(candidate);
    } catch {
      continue;
    }
    if (real === tmpReal || real.startsWith(tmpReal + path.sep)) continue;
    try {
      await fs.access(real);
      return real;
    } catch {
      // try the next one
    }
  }
  throw new Error('no writable directory outside the temporary area');
}

export async function makeSandbox() {
  const base = await fs.mkdtemp(path.join(await outsideBase(), '.cdm-case-'));
  const root = path.join(base, 'ws');
  const outside = path.join(base, 'outside');
  await fs.mkdir(root);
  await fs.mkdir(outside);
  return {
    base,
    root,
    outside,
    async cleanup() {
      await fs.rm(base, {recursive: true, force: true});
    },
  };
}

function makePage(calls) {
  const page = {
    ...listener(),
    url() {
      return 'about:blank';
    },
    isClosed() {
      return false;
    },
    frames() {
      return [];
    },
    viewport() {
      return null;
    },
    async screenshot(options) {
      calls.screenshot.push(options ?? {});
      return Buffer.from('PNG-PAYLOAD');
    },
    async captureHeapSnapshot(options) {
      calls.captureHeapSnapshot.push(options ?? {});
      if (options?.path) {
        await fs.writeFile(options.path, 'HEAP-PAYLOAD');
      }
    },
    async screencast(options) {
      calls.screencast.push(options ?? {});
      return {
        async stop() {},
      };
    },
    browserContext() {
      return page.__context;
    },
    async hasDevTools() {
      return false;
    },
    async emulateFocusedPage() {},
    setDefaultTimeout() {},
    setDefaultNavigationTimeout() {},
    async setViewport() {},
    async setExtraHTTPHeaders() {},
    async emulateCPUThrottling() {},
    async emulateNetworkConditions() {},
    _client() {
      return {
        ...listener(),
        send() {},
        target() {
          return {_targetId: 'target-1'};
        },
      };
    },
  };
  return page;
}

export async function makeMcp(options = {}) {
  const calls = {
    installExtension: [],
    screenshot: [],
    captureHeapSnapshot: [],
    screencast: [],
  };
  const extensions = [...(options.extensions ?? [])];

  const page = makePage(calls);
  const defaultContext = {
    pages: async () => [page],
    browserContexts() {
      return [defaultContext];
    },
  };
  page.__context = defaultContext;

  const browser = {
    ...listener(),
    pages: async () => [page],
    targets: () => [],
    browserContexts: () => [defaultContext],
    defaultBrowserContext: () => defaultContext,
    isConnected() {
      return true;
    },
    async installExtension(extensionPath) {
      calls.installExtension.push(extensionPath);
      return 'extension-id';
    },
    async extensions() {
      const map = new Map();
      for (const extension of extensions) map.set(extension.id, extension);
      return map;
    },
    async uninstallExtension() {},
    async triggerExtensionAction() {},
  };

  const context = new McpContext(
    browser,
    () => {},
    {experimentalDevToolsDebugging: false, performanceCrux: false},
    Locator,
  );
  await context.createPagesSnapshot();

  const tools = createTools(TOOL_ARGS);
  const byName = new Map(tools.map(tool => [tool.name, tool]));
  const mutex = new Mutex();

  return {
    context,
    page,
    calls,
    setExtensions(list) {
      extensions.length = 0;
      extensions.push(...list);
    },
    setRoots(roots) {
      context.setRoots(roots);
    },
    setRootDir(dir) {
      context.setRoots([{uri: pathToFileURL(dir).href, name: 'workspace'}]);
    },
    async call(name, params) {
      const tool = byName.get(name);
      if (!tool) throw new Error(`tool ${name} is not registered`);
      const handler = new ToolHandler(
        tool,
        TOOL_ARGS,
        async () => context,
        mutex,
      );
      return await handler.handle(params ?? {});
    },
  };
}

export function resultText(result) {
  const content = result?.content ?? [];
  return content
    .map(part => (part.type === 'text' ? part.text : '[non-text]'))
    .join('\n');
}

export function isError(result) {
  return result?.isError === true;
}

export async function exists(p) {
  try {
    await fs.lstat(p);
    return true;
  } catch {
    return false;
  }
}

export async function readIfExists(p) {
  try {
    return await fs.readFile(p, 'utf-8');
  } catch {
    return undefined;
  }
}
