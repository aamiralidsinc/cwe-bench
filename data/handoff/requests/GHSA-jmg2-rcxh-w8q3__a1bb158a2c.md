<!-- label=GHSA-jmg2-rcxh-w8q3 hash=a1bb158a2c -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-jmg2-rcxh-w8q3
- CVE: CVE-2026-61782
- CWE: CWE-200
- Ecosystem / Package: npm / @rsdoctor/rspack-plugin
- Repository: https://github.com/web-infra-dev/rsdoctor
- Official Summary: @rsdoctor/rspack-plugin has Unauthenticated HTTP API that Exposes Project Source Code and Build Metadata

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/packages/cli/src/commands/analyze.ts b/packages/cli/src/commands/analyze.ts
index 61b5c5301e8ce61b78e66928fa7e8232b2714130..e358af6cb09aa1745759756a335729c1ce39c908 100644
--- a/packages/cli/src/commands/analyze.ts
+++ b/packages/cli/src/commands/analyze.ts
@@ -70,7 +70,16 @@ example: ${bin} ${Commands.Analyze} --profile "${Constants.RsdoctorOutputManifes
 
       spinner.text = `start server`;
 
-      const sdk = new RsdoctorSDK({ name, root: cwd, port, type });
+      const sdk = new RsdoctorSDK({
+        name,
+        root: cwd,
+        type,
+        config: {
+          server: {
+            port,
+          },
+        },
+      });
 
       await sdk.bootstrap();
 
@@ -78,7 +87,12 @@ example: ${bin} ${Commands.Analyze} --profile "${Constants.RsdoctorOutputManifes
       sdk.getManifestData = () => json;
 
       const manifestBuffer = Buffer.from(
-        JSON.stringify({ ...json, __LOCAL__SERVER__: true }),
+        JSON.stringify({
+          ...json,
+          __LOCAL__SERVER__: true,
+          __SOCKET__PORT__: sdk.server.socketUrl.port.toString(),
+          __SOCKET__URL__: sdk.server.socketUrl.socketUrl,
+        }),
       );
 
       sdk.server.proxy(SDK.ServerAPI.API.Manifest, 'GET', () => manifestBuffer);
diff --git a/packages/cli/src/commands/stats-analyze.test.ts b/packages/cli/src/commands/stats-analyze.test.ts
new file mode 100644
index 0000000000000000000000000000000000000000..389c6971578d3c5614c35d6a4f47bd075f9642e3
--- /dev/null
+++ b/packages/cli/src/commands/stats-analyze.test.ts
@@ -0,0 +1,17 @@
+import { describe, expect, it } from '@rstest/core';
+import { coercePort } from './stats-analyze';
+
+describe('stats-analyze command', () => {
+  it('coercePort() preserves undefined', () => {
+    expect(coercePort()).toBeUndefined();
+  });
+
+  it('coercePort() converts valid port values to numbers', () => {
+    expect(coercePort(8888)).toBe(8888);
+    expect(coercePort('8888')).toBe(8888);
+  });
+
+  it('coercePort() rejects invalid port values', () => {
+    expect(() => coercePort('foo')).toThrow('Invalid port: foo');
+  });
+});
diff --git a/packages/cli/src/commands/stats-analyze.ts b/packages/cli/src/commands/stats-analyze.ts
index 916d156ba973904b7b7a45f3748304bc8f45fd46..618d37a83b283b4930e490fa28b894d813495070 100644
--- a/packages/cli/src/commands/stats-analyze.ts
+++ b/packages/cli/src/commands/stats-analyze.ts
@@ -11,10 +11,23 @@ import { TransUtils } from '@rsdoctor/graph';
 interface Options {
   profile: string;
   open?: boolean;
-  port?: number;
+  port?: number | string;
   type?: SDK.ToDataType;
 }
 
+export function coercePort(port?: number | string) {
+  if (typeof port === 'undefined') {
+    return undefined;
+  }
+
+  const value = Number(port);
+  if (!Number.isFinite(value)) {
+    throw new Error(`Invalid port: ${port}`);
+  }
+
+  return value;
+}
+
 export const statsAnalyze: Command<
   Commands.StatsAnalyze,
   Options,
@@ -32,7 +45,8 @@ export const statsAnalyze: Command<
       .option('--port <number>', 'port for Rsdoctor Server')
       .option('--type <mode>', 'Bundle analysis mode (normal or lite)');
   },
-  async action({ profile, open = true, type = SDK.ToDataType.Normal }) {
+  async action({ profile, open = true, port, type = SDK.ToDataType.Normal }) {
+    const serverPort = coercePort(port);
     const spinner = ora({ prefixText: cyan(`[${name}]`) }).start(
       `start to loading "${profile}"`,
     );
@@ -46,7 +60,11 @@ export const statsAnalyze: Command<
       name: 'stats-analyze',
       root: process.cwd(),
       type,
-      noServer: false,
+      config: {
+        server: {
+          port: serverPort,
+        },
+      },
     });
 
     await sdk.bootstrap();
diff --git a/packages/components/src/utils/data/local.ts b/packages/components/src/utils/data/local.ts
index d5f8838848d1e8d90918cf821fed8fb86f9037d0..7249ac27fd0aad4e818331766f26666d01b79be3 100644
--- a/packages/components/src/utils/data/local.ts
+++ b/packages/components/src/utils/data/local.ts
@@ -70,6 +70,7 @@ export class LocalServerDataLoader extends BaseDataLoader {
     // request limitation key
     const key = body ? `${api}_${JSON.stringify(body)}` : `${api}`;
     const socketPort = this.get('__SOCKET__PORT__') ?? '';
+    const socketUrl = this.get('__SOCKET__URL__') ?? '';
 
     return this.limit(key, async () => {
       try {
@@ -77,6 +78,7 @@ export class LocalServerDataLoader extends BaseDataLoader {
           api,
           body as SDK.ServerAPI.InferRequestBodyType<T>,
           socketPort,
+          socketUrl,
         )) as R;
       } catch (err) {
         this.log(`loadAPI error: `, key);
@@ -121,7 +123,8 @@ export class LocalServerDataLoader extends BaseDataLoader {
 
     subscription.listeners.add(fn);
     const socketPort = this.get('__SOCKET__PORT__') ?? '';
-    subscribeServerAPI(api, normalizedBody, fn, socketPort);
+    const socketUrl = this.get('__SOCKET__URL__') ?? '';
+    subscribeServerAPI(api, normalizedBody, fn, socketPort, socketUrl);
   }
 
   public removeOnDataUpdate<
@@ -133,7 +136,8 @@ export class LocalServerDataLoader extends BaseDataLoader {
   ) {
     const key = `${api}::${JSON.stringify(body ?? null)}`;
     const socketPort = this.get('__SOCKET__PORT__') ?? '';
-    unsubscribeServerAPI(api, body, fn, socketPort);
+    const socketUrl = this.get('__SOCKET__URL__') ?? '';
+    unsubscribeServerAPI(api, body, fn, socketPort, socketUrl);
     this.events.get(key)?.listeners.delete(fn);
   }
 }
diff --git a/packages/components/src/utils/socket.ts b/packages/components/src/utils/socket.ts
index 8ac102b9d76e177cde5a50f8f820d94f822fd628..ff41392450d7156e01698ce9840f170ae643e0a4 100644
--- a/packages/components/src/utils/socket.ts
+++ b/packages/components/src/utils/socket.ts
@@ -63,7 +63,11 @@ function getDefaultSocketUrl() {
     : `${socketProtocol}://${location.host}`;
 }
 
-function getSocketUrl(socketPort?: string) {
+function getSocketUrl(socketPort?: string, socketUrl?: string) {
+  if (socketUrl) {
+    return socketUrl;
+  }
+
   if (typeof location === 'undefined') {
     return socketPort ? `ws://localhost:${socketPort}` : '';
   }
@@ -201,9 +205,14 @@ export function requestServerAPI<
     SDK.ServerAPI.InferRequestBodyType<T>,
   R extends SDK.ServerAPI.InferResponseType<T> =
     SDK.ServerAPI.InferResponseType<T>,
->(api: T, body: B | null | undefined, socketPort?: string): Promise<R> {
-  const socketUrl = getSocketUrl(socketPort);
-  if (!socketUrl) {
+>(
+  api: T,
+  body: B | null | undefined,
+  socketPort?: string,
+  socketUrl?: string,
+): Promise<R> {
+  const resolvedSocketUrl = getSocketUrl(socketPort, socketUrl);
+  if (!resolvedSocketUrl) {
     return Promise.reject(new Error('WebSocket URL is not available.'));
   }
 
@@ -211,7 +220,7 @@ export function requestServerAPI<
     return Promise.reject(new Error('WebSocket is not available.'));
   }
 
-  const client = getClient(socketUrl);
+  const client = getClient(resolvedSocketUrl);
   const id = `${Date.now()}-${++requestId}`;
 
   return new Promise<R>((resolve, reject) => {
@@ -235,8 +244,9 @@ export function subscribeServerAPI<T extends SocketAPI>(
   body: SDK.ServerAPI.InferRequestBodyType<T, null> | null,
   listener: SocketListener<T>,
   socketPort?: string,
+  socketUrl?: string,
 ) {
-  const client = getClient(getSocketUrl(socketPort));
+  const client = getClient(getSocketUrl(socketPort, socketUrl));
   const bodyValue = body ?? null;
   const key = getSubscriptionKey(api, bodyValue);
   if (!client.listeners.has(key)) {
@@ -253,7 +263,7 @@ export function subscribeServerAPI<T extends SocketAPI>(
   sendSubscription(client, subscription);
 
   return () => {
-    unsubscribeServerAPI(api, bodyValue, listener, socketPort);
+    unsubscribeServerAPI(api, bodyValue, listener, socketPort, socketUrl);
   };
 }
 
@@ -262,8 +272,9 @@ export function unsubscribeServerAPI<T extends SocketAPI>(
   body: SDK.ServerAPI.InferRequestBodyType<T, null> | null,
   listener: SocketListener<T>,
   socketPort?: string,
+  socketUrl?: string,
 ) {
-  const client = getClient(getSocketUrl(socketPort));
+  const client = getClient(getSocketUrl(socketPort, socketUrl));
   const key = getSubscriptionKey(api, body);
   const listeners = client.listeners.get(key);
   listeners?.delete(listener as SocketListener);
diff --git a/packages/core/src/inner-plugins/utils/config.ts b/packages/core/src/inner-plugins/utils/config.ts
index 9483c79e088038af38c54b002af535c3d8cfda43..4ae82376d37a0692cd138ee0710b5a2042ac21fe 100644
--- a/packages/core/src/inner-plugins/utils/config.ts
+++ b/packages/core/src/inner-plugins/utils/config.ts
@@ -101,6 +101,7 @@ export function normalizeUserConfig<Rules extends Linter.ExtendRuleData[]>(
     output = outputConfig,
     supports = getDefaultSupports(),
     port,
+    server: userServer = {},
     printLog = { serverUrls: true },
     mode = undefined,
     brief = undefined,
@@ -117,6 +118,15 @@ export function normalizeUserConfig<Rules extends Linter.ExtendRuleData[]>(
   assert(typeof features === 'object' || Array.isArray(features));
   assert(typeof loaderInterceptorOptions === 'object');
   assert(typeof disableClientServer === 'boolean');
+  assert(typeof port === 'undefined' || typeof port === 'number');
+  assert(typeof userServer === 'object' && userServer !== null);
+  const server: SDK.RsdoctorServerConfig = {
+    ...userServer,
+  };
+  assert(typeof server.port === 'undefined' || typeof server.port === 'number');
+  if (typeof server.port === 'undefined' && typeof port !== 'undefined') {
+    server.port = port;
+  }
   let finalMode: keyof typeof SDK.IMode =
     ('mode' in output && isValidMode(output.mode)
       ? output.mode === ('lite' as SDK.IMode.normal)
@@ -174,6 +184,7 @@ export function normalizeUserConfig<Rules extends Linter.ExtendRuleData[]>(
     innerClientPath,
     supports,
     port,
+    server,
     printLog,
   };
 
diff --git a/packages/rspack-plugin/src/multiple.ts b/packages/rspack-plugin/src/multiple.ts
index 00a907e948935188fe9b47201201e7dbbdad34b6..6c8b4ef52ebf9ace4a57c4efead78c44cca08968 100644
--- a/packages/rspack-plugin/src/multiple.ts
+++ b/packages/rspack-plugin/src/multiple.ts
@@ -32,6 +32,7 @@ export class RsdoctorRspackMultiplePlugin<
       extraConfig: {
         innerClientPath: normallizedOptions.innerClientPath,
         printLog: normallizedOptions.printLog,
+        server: normallizedOptions.server,
         mode: normallizedOptions.output.mode
           ? normallizedOptions.output.mode
           : undefined,
diff --git a/packages/rspack-plugin/src/plugin.ts b/packages/rspack-plugin/src/plugin.ts
index 92bc658c9b9fa4a9a9bd7069b5e21729a6eb790c..900488d2c0ac028b260251783c10cf545b6a00e5 100644
--- a/packages/rspack-plugin/src/plugin.ts
+++ b/packages/rspack-plugin/src/plugin.ts
@@ -67,7 +67,7 @@ export class RsdoctorRspackPlugin<
         },
       }),
     );
-    const { port, output, innerClientPath, printLog, sdkInstance } =
+    const { port, server, output, innerClientPath, printLog, sdkInstance } =
       this.options;
 
     this.sdk =
@@ -80,6 +80,7 @@ export class RsdoctorRspackPlugin<
         config: {
           innerClientPath,
           printLog,
+          server,
           mode: output.mode ? output.mode : undefined,
           brief:
             output.mode === SDK.IMode[SDK.IMode.brief]
diff --git a/packages/rspack-plugin/tests/plugin.test.ts b/packages/rspack-plugin/tests/plugin.test.ts
new file mode 100644
index 0000000000000000000000000000000000000000..f8894d60b5540ddf963cf65a06a845cb11f6d802
--- /dev/null
+++ b/packages/rspack-plugin/tests/plugin.test.ts
@@ -0,0 +1,31 @@
+import { describe, expect, it } from '@rstest/core';
+import { RsdoctorRspackPlugin } from '../src/plugin';
+
+describe('RsdoctorRspackPlugin', () => {
+  it('keeps the report server when the client server is disabled in CI', () => {
+    const originalCI = process.env.CI;
+    const originalRSTEST = process.env.RSTEST;
+
+    try {
+      process.env.CI = 'true';
+      delete process.env.RSTEST;
+
+      const plugin = new RsdoctorRspackPlugin();
+
+      expect(plugin.options.disableClientServer).toBe(true);
+      expect(plugin.sdk.server.constructor.name).toBe('RsdoctorServer');
+    } finally {
+      if (typeof originalCI === 'undefined') {
+        delete process.env.CI;
+      } else {
+        process.env.CI = originalCI;
+      }
+
+      if (typeof originalRSTEST === 'undefined') {
+        delete process.env.RSTEST;
+      } else {
+        process.env.RSTEST = originalRSTEST;
+      }
+    }
+  });
+});
diff --git a/packages/sdk/src/sdk/multiple/primary.ts b/packages/sdk/src/sdk/multiple/primary.ts
index a7570cc81f38026162a47737a09390fea7e736ba..e94219a3873271b35d5784d376d4877e17c22988 100644
--- a/packages/sdk/src/sdk/multiple/primary.ts
+++ b/packages/sdk/src/sdk/multiple/primary.ts
@@ -42,16 +42,24 @@ export class RsdoctorPrimarySDK
     extraConfig,
     type,
   }: RsdoctorSlaveSDKOptions) {
-    super({ name, root: controller.root });
+    super({
+      name,
+      root: controller.root,
+      config: extraConfig,
+    });
 
     const lastSdk = controller.getLastSdk();
-    const port = lastSdk ? lastSdk.server.port + 1 : this.server.port;
+    const port = lastSdk
+      ? lastSdk.server.port + 1
+      : (extraConfig?.server?.port ?? this.server.port);
 
     this.id = id++;
     this.stage = typeof stage === 'number' ? stage : 1;
     this.extraConfig = extraConfig;
     this.parent = controller;
-    this.server = new RsdoctorSlaveServer(this, port);
+    this.server = new RsdoctorSlaveServer(this, port, {
+      cors: extraConfig?.server?.cors,
+    });
     this.type = type;
     this.setName(name);
     this.clearSwitch();
diff --git a/packages/sdk/src/sdk/multiple/server.ts b/packages/sdk/src/sdk/multiple/server.ts
index db4d37ebe3756c2fe27c035edbf5aecdaf826fe2..0e758ecfa9bd9b3d5d50eaa7f5e9bbbb338a4a4b 100644
--- a/packages/sdk/src/sdk/multiple/server.ts
+++ b/packages/sdk/src/sdk/multiple/server.ts
@@ -1,12 +1,16 @@
 import { Server } from '@rsdoctor/utils/build';
-import { RsdoctorServer } from '../server';
+import { RsdoctorServer, type RsdoctorServerOptions } from '../server';
 import type { RsdoctorPrimarySDK } from './primary';
 
 export class RsdoctorSlaveServer extends RsdoctorServer {
   protected sdk: RsdoctorPrimarySDK;
 
-  constructor(sdk: RsdoctorPrimarySDK, port = Server.defaultPort) {
-    super(sdk, port);
+  constructor(
+    sdk: RsdoctorPrimarySDK,
+    port = Server.defaultPort,
+    config?: RsdoctorServerOptions,
+  ) {
+    super(sdk, port, config);
     this.sdk = sdk;
   }
 
diff --git a/packages/sdk/src/sdk/sdk/index.ts b/packages/sdk/src/sdk/sdk/index.ts
index 7a62e1836f4d83e5c43953a543a15b2ffc0e0365..40c171693e473636635be26b4a7cf718875394fa 100644
--- a/packages/sdk/src/sdk/sdk/index.ts
+++ b/packages/sdk/src/sdk/sdk/index.ts
@@ -60,11 +60,14 @@ export class RsdoctorSDK<
 
   constructor(options: T) {
     super(options);
+    const serverConfig = options.config?.server;
+    const port = serverConfig?.port ?? options.port;
     this.server = options.config?.noServer
-      ? new RsdoctorFakeServer(this, undefined)
-      : new RsdoctorServer(this, options.port, {
+      ? new RsdoctorFakeServer(this, port)
+      : new RsdoctorServer(this, port, {
           innerClientPath: options.config?.innerClientPath || '',
           printServerUrl: options.config?.printLog?.serverUrls,
+          cors: serverConfig?.cors,
         });
     this.type = Lodash.isNumber(options.type)
       ? options.type
diff --git a/packages/sdk/src/sdk/server/fakeServer.ts b/packages/sdk/src/sdk/server/fakeServer.ts
index 419b0849731f06c332720e9776f67fd11708f384..f3365702433c2e3a328506d38b9a291bed66ec6c 100644
--- a/packages/sdk/src/sdk/server/fakeServer.ts
+++ b/packages/sdk/src/sdk/server/fakeServer.ts
@@ -11,5 +11,9 @@ export class RsdoctorFakeServer extends RsdoctorServer {
     this.sdk = sdk;
   }
 
+  async bootstrap() {}
+
   async openClientPage() {}
+
+  dispose = async () => {};
 }
diff --git a/packages/sdk/src/sdk/server/index.ts b/packages/sdk/src/sdk/server/index.ts
index d1f4c3d4463176a0ba8e53c04bad4c5779b33e19..adf2397c70dc871c5af8cc692a8917dc759e9148 100644
--- a/packages/sdk/src/sdk/server/index.ts
+++ b/packages/sdk/src/sdk/server/index.ts
@@ -12,18 +12,34 @@ import * as APIs from './apis';
 import { chalk, logger } from '@rsdoctor/utils/logger';
 import { openBrowser } from '@/sdk/utils/openBrowser';
 import path from 'path';
-import { getLocalIpAddress } from './utils';
 import { Lodash } from '@rsdoctor/utils/common';
 import { createRequire } from 'module';
 import { ServerResponse } from 'http';
+import { randomBytes } from 'crypto';
+import {
+  DEFAULT_ALLOWED_CORS_ORIGINS,
+  isAllowedCorsRequest,
+  isAllowedRequestHost,
+} from './security';
 
 const require = createRequire(import.meta.url);
 export * from './utils';
 
 /** Path for launch-editor: open file in editor from the UI (see https://github.com/yyx990803/launch-editor) */
 const OPEN_IN_EDITOR_PATH = '/__open-in-editor';
+const LISTEN_RETRY_LIMIT = 10;
 
-export type ISocketType = { port: number; socketUrl: string };
+export type ISocketType = { port: number; socketUrl: string; token: string };
+
+export type RsdoctorServerOptions = {
+  innerClientPath?: string;
+  printServerUrl?: boolean;
+  cors?: SDK.RsdoctorServerConfig['cors'];
+};
+
+function isAddressInUseError(error: unknown) {
+  return (error as { code?: string }).code === 'EADDRINUSE';
+}
 
 export class RsdoctorServer implements SDK.RsdoctorServerInstance {
   private _server!: Common.PromiseReturnType<typeof Server.createServer>;
@@ -40,10 +56,14 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
 
   private _printServerUrl: boolean;
 
+  private _cors: SDK.RsdoctorServerConfig['cors'];
+
+  private _socketToken = randomBytes(16).toString('hex');
+
   constructor(
     protected sdk: SDK.RsdoctorBuilderSDKInstance,
     port = Server.defaultPort,
-    config?: { innerClientPath?: string; printServerUrl?: boolean },
+    config?: RsdoctorServerOptions,
   ) {
     assert(typeof port === 'number');
     // maybe the port will be rewrite in bootstrap()
@@ -53,6 +73,7 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
     this._printServerUrl = Lodash.isUndefined(config?.printServerUrl)
       ? true
       : config?.printServerUrl;
+    this._cors = config?.cors;
   }
 
   public get app(): SDK.RsdoctorServerInstance['app'] {
@@ -60,8 +81,7 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
   }
 
   public get host(): string {
-    const host = getLocalIpAddress();
-    return host;
+    return Server.defaultHost;
   }
 
   public get origin(): string {
@@ -71,7 +91,8 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
   public get socketUrl(): ISocketType {
     return {
       port: this.port,
-      socketUrl: `ws://localhost:${this.port}`,
+      socketUrl: `ws://localhost:${this.port}?token=${this._socketToken}`,
+      token: this._socketToken,
     };
   }
 
@@ -79,19 +100,66 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
     return this._innerClientPath;
   }
 
+  private async createInnerServer() {
+    let expectedPort = this.port;
+    let lastError: unknown;
+
+    for (let retry = 0; retry < LISTEN_RETRY_LIMIT; retry++) {
+      const port = Server.getPortSync(expectedPort, this.host);
+
+      try {
+        return {
+          port,
+          server: await Server.createServer(port, this.host),
+        };
+      } catch (error) {
+        if (!isAddressInUseError(error)) {
+          throw error;
+        }
+        lastError = error;
+        expectedPort = port + 1;
+      }
+    }
+
+    throw lastError;
+  }
+
+  private resolveCorsOptions(): false | SDK.RsdoctorServerCorsOptions {
+    if (this._cors === false) {
+      return false;
+    }
+    if (this._cors === true) {
+      return {};
+    }
+    if (typeof this._cors === 'undefined') {
+      return {
+        origin: DEFAULT_ALLOWED_CORS_ORIGINS,
+      };
+    }
+    return {
+      ...this._cors,
+      origin:
+        typeof this._cors.origin === 'undefined'
+          ? DEFAULT_ALLOWED_CORS_ORIGINS
+          : this._cors.origin,
+    };
+  }
+
   async bootstrap() {
     if (!this.disposed) {
       return;
     }
 
-    const port = Server.getPortSync(this.port);
+    const { port, server } = await this.createInnerServer();
+    const corsOptions = this.resolveCorsOptions();
     // rewrite port when the default port is unavailable
     this.port = port;
-    this._server = await Server.createServer(port);
+    this._server = server;
     this._socket = new Socket({
       sdk: this.sdk,
       server: this._server.server,
       port: this.port,
+      token: this._socketToken,
     });
     await this._socket.bootstrap();
 
@@ -103,8 +171,37 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
 
     this.disposed = false;
 
-    this.app.use(cors());
+    this.app.use((req, res, next) => {
+      const host = req.headers.host || req.headers[':authority'];
+      if (!isAllowedRequestHost(host)) {
+        res.statusCode = 403;
+        res.end();
+        return;
+      }
+
+      next();
+    });
+    if (
+      corsOptions !== false &&
+      corsOptions.origin === DEFAULT_ALLOWED_CORS_ORIGINS
+    ) {
+      this.app.use((req, res, next) => {
+        const host = req.headers.host || req.headers[':authority'];
+        if (!isAllowedCorsRequest(req.headers.origin, host)) {
+          res.statusCode = 403;
+          res.end();
+          return;
+        }
+
+        next();
+      });
+    }
+    if (corsOptions !== false) {
+      this.app.use(cors(corsOptions));
+    }
     this.app.use(bodyParser.json({ limit: '500mb' }));
+    await this._router.setup();
+
     const clientHtmlPath = this._innerClientPath
       ? this._innerClientPath
       : require.resolve('@rsdoctor/client');
@@ -168,8 +265,6 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
       },
     );
 
-    await this._router.setup();
-
     process.once('exit', () => this.dispose());
     process.once('SIGINT', () => this.dispose(0));
     process.once('SIGTERM', () => this.dispose(0));
@@ -199,9 +294,6 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
       if (m === method) {
         try {
           const body = await cb(req, res, next);
-
-          res.setHeader('Access-Control-Allow-Origin', '*');
-          res.setHeader('Access-Control-Allow-Credentials', 'true');
           res.statusCode = 200;
 
           if (Buffer.isBuffer(body)) {
@@ -324,14 +416,15 @@ export class RsdoctorServer implements SDK.RsdoctorServerInstance {
     }
     this.disposed = true;
 
-    if (this._socket) {
-      this._socket.dispose();
-    }
-
     if (this._server) {
       await this._server.close();
     }
 
+    // Close sockets after the HTTP server stops accepting new connections.
+    if (this._socket) {
+      this._socket.dispose();
+    }
+
     if (exitCode !== undefined) {
       process.exit(exitCode);
     }
diff --git a/packages/sdk/src/sdk/server/security.ts b/packages/sdk/src/sdk/server/security.ts
new file mode 100644
index 0000000000000000000000000000000000000000..b58896942befdbbdebea2a1320095b4c22aa5c33
--- /dev/null
+++ b/packages/sdk/src/sdk/server/security.ts
@@ -0,0 +1,74 @@
+import { isIP } from 'node:net';
+
+export const DEFAULT_ALLOWED_CORS_ORIGINS =
+  /^https?:\/\/(?:(?:[^:]+\.)?localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/;
+
+const LOCAL_HOSTNAMES = /^(?:localhost|[^:]+\.localhost)$/;
+
+export function isAllowedRequestOrigin(origin: string | string[] | undefined) {
+  if (origin === undefined) {
+    return true;
+  }
+
+  return (
+    typeof origin === 'string' && DEFAULT_ALLOWED_CORS_ORIGINS.test(origin)
+  );
+}
+
+function getHostnameFromOrigin(origin: string) {
+  try {
+    const hostname = new URL(origin).hostname.toLowerCase();
+    return hostname.startsWith('[') && hostname.endsWith(']')
+      ? hostname.slice(1, -1)
+      : hostname;
+  } catch {
+    return '';
+  }
+}
+
+function isIpAddress(hostname: string) {
+  return isIP(hostname) !== 0;
+}
+
+function getHostnameFromHost(host: string) {
+  if (host.startsWith('[')) {
+    const endIndex = host.indexOf(']');
+    return endIndex === -1 ? '' : host.slice(1, endIndex);
+  }
+
+  return host.split(':')[0];
+}
+
+export function isAllowedRequestHost(host: string | string[] | undefined) {
+  if (typeof host !== 'string') {
+    return false;
+  }
+
+  const hostname = getHostnameFromHost(host).toLowerCase();
+  return LOCAL_HOSTNAMES.test(hostname) || isIpAddress(hostname);
+}
+
+export function isAllowedCorsRequest(
+  origin: string | string[] | undefined,
+  host: string | string[] | undefined,
+) {
+  if (origin === undefined) {
+    return true;
+  }
+  if (
+    typeof origin !== 'string' ||
+    typeof host !== 'string' ||
+    !isAllowedRequestOrigin(origin)
+  ) {
+    return false;
+  }
+
+  const originHostname = getHostnameFromOrigin(origin);
+  const hostHostname = getHostnameFromHost(host).toLowerCase();
+
+  if (originHostname.endsWith('.localhost')) {
+    return originHostname === hostHostname;
+  }
+
+  return true;
+}
diff --git a/packages/sdk/src/sdk/server/socket/index.ts b/packages/sdk/src/sdk/server/socket/index.ts
index bd92a2030e81d8829289badbd8d8dc59a45a641f..14b481ceb4f8bd14a517b728c323c750027c8207 100644
--- a/packages/sdk/src/sdk/server/socket/index.ts
+++ b/packages/sdk/src/sdk/server/socket/index.ts
@@ -1,12 +1,15 @@
 import { Common, SDK } from '@rsdoctor/types';
 import type { Server } from 'http';
 import WebSocket, { WebSocketServer } from 'ws';
+import type { VerifyClientCallbackSync } from 'ws';
 import { SocketAPILoader } from './api';
+import { isAllowedRequestHost } from '../security';
 
 interface SocketOptions {
   sdk: SDK.RsdoctorBuilderSDKInstance;
   server: Server;
   port: number;
+  token: string;
 }
 
 type Subscription = {
@@ -25,6 +28,14 @@ type ClientMessage = {
   body?: Common.PlainObject | null;
 };
 
+function isAllowedSocketToken(url: string | undefined, token: string) {
+  if (!url) {
+    return false;
+  }
+
+  return new URL(url, 'http://localhost').searchParams.get('token') === token;
+}
+
 export class Socket {
   protected server?: WebSocketServer;
 
@@ -41,7 +52,16 @@ export class Socket {
   }
 
   public bootstrap() {
-    this.server = new WebSocketServer({ server: this.options.server });
+    this.server = new WebSocketServer({
+      server: this.options.server,
+      verifyClient: (({ req }) => {
+        const host = req.headers.host || req.headers[':authority'];
+        return (
+          isAllowedRequestHost(host) &&
+          isAllowedSocketToken(req.url, this.options.token)
+        );
+      }) satisfies VerifyClientCallbackSync,
+    });
     this.server.on('connection', (client) => {
       this.attachClient(client);
     });
diff --git a/packages/sdk/tests/sdk/core/atomic-write.test.ts b/packages/sdk/tests/sdk/core/atomic-write.test.ts
index c0ecad8da0204cb808426c338d6a77642e49f693..ac4bdaeacdf0844dafa8f8a001af3aa0c0ab27f1 100644
--- a/packages/sdk/tests/sdk/core/atomic-write.test.ts
+++ b/packages/sdk/tests/sdk/core/atomic-write.test.ts
@@ -62,8 +62,12 @@ describe('atomic write manifest', () => {
           const sdk = new RsdoctorSDK({
             name: 'test',
             root: process.cwd(),
-            port,
-            config: { noServer: true },
+            config: {
+              noServer: true,
+              server: {
+                port,
+              },
+            },
           });
 
           try {
diff --git a/packages/sdk/tests/server/apis/project.test.ts b/packages/sdk/tests/server/apis/project.test.ts
index 93f12a4107416d5f6e37332ca15578bac8ab18f7..d1f8ecce9254f3f8d8eac4476ef5753dc16ab41e 100644
--- a/packages/sdk/tests/server/apis/project.test.ts
+++ b/packages/sdk/tests/server/apis/project.test.ts
@@ -1,13 +1,91 @@
 import { describe, it, expect, rs } from '@rstest/core';
 import { Manifest, SDK } from '@rsdoctor/types';
 import { Manifest as ManifestShared } from '@rsdoctor/utils/common';
-import { cwd, setupSDK } from '../../utils';
+import { request } from 'http';
+import { cwd, setupSDK, type MockSDKResponse } from '../../utils';
 import { getLocalIpAddress } from '../../../src/sdk/server/utils';
 
 rs.setConfig({ testTimeout: 50000 });
 
 describe('test server/apis/project.ts', () => {
   const target = setupSDK();
+  const customCorsTarget = setupSDK({
+    server: {
+      cors: {
+        origin: 'https://example.com',
+      },
+    },
+  });
+  const partialCorsTarget = setupSDK({
+    server: {
+      cors: {
+        credentials: true,
+      },
+    },
+  });
+
+  function optionsWithOrigin(
+    target: MockSDKResponse,
+    origin: string,
+    host?: string,
+  ) {
+    return new Promise<{
+      statusCode: number;
+      allowOrigin: string | string[] | undefined;
+    }>((resolve, reject) => {
+      const url = new URL(
+        `${target.server.origin}${SDK.ServerAPI.API.Manifest}`,
+      );
+      const req = request(
+        {
+          hostname: url.hostname,
+          port: url.port,
+          path: url.pathname,
+          method: 'OPTIONS',
+          headers: {
+            Origin: origin,
+            ...(host ? { Host: host } : {}),
+          },
+        },
+        (res) => {
+          res.on('data', () => {});
+          res.on('close', () => {
+            resolve({
+              statusCode: res.statusCode || 0,
+              allowOrigin: res.headers['access-control-allow-origin'],
+            });
+          });
+        },
+      );
+
+      req.on('error', reject);
+      req.end();
+    });
+  }
+
+  function requestWithHost(pathname: string, host: string) {
+    return new Promise<{ statusCode: number }>((resolve, reject) => {
+      const url = new URL(`${target.server.origin}${pathname}`);
+      const req = request(
+        {
+          hostname: url.hostname,
+          port: url.port,
+          path: `${url.pathname}${url.search}`,
+          method: 'GET',
+          headers: { Host: host },
+        },
+        (res) => {
+          res.on('data', () => {});
+          res.on('close', () => {
+            resolve({ statusCode: res.statusCode || 0 });
+          });
+        },
+      );
+
+      req.on('error', reject);
+      req.end();
+    });
+  }
 
   it(`test api: ${SDK.ServerAPI.API.Env}`, async () => {
     const env = (await target.get(SDK.ServerAPI.API.Env)).toJSON();
@@ -16,6 +94,103 @@ describe('test server/apis/project.ts', () => {
     expect(env.port).toEqual(target.server.port);
   });
 
+  it('uses local origins for default CORS preflight requests', async () => {
+    await expect(
+      optionsWithOrigin(target, 'https://example.com'),
+    ).resolves.toStrictEqual({
+      statusCode: 403,
+      allowOrigin: undefined,
+    });
+
+    await expect(
+      optionsWithOrigin(target, `http://127.0.0.1:${target.server.port}`),
+    ).resolves.toStrictEqual({
+      statusCode: 204,
+      allowOrigin: `http://127.0.0.1:${target.server.port}`,
+    });
+
+    await expect(
+      optionsWithOrigin(target, `http://127.0.0.1:${target.server.port + 1}`),
+    ).resolves.toStrictEqual({
+      statusCode: 204,
+      allowOrigin: `http://127.0.0.1:${target.server.port + 1}`,
+    });
+
+    await expect(
+      optionsWithOrigin(target, `http://foo.localhost:${target.server.port}`),
+    ).resolves.toStrictEqual({
+      statusCode: 403,
+      allowOrigin: undefined,
+    });
+
+    await expect(
+      optionsWithOrigin(
+        target,
+        `http://foo.localhost:${target.server.port}`,
+        `foo.localhost:${target.server.port}`,
+      ),
+    ).resolves.toStrictEqual({
+      statusCode: 204,
+      allowOrigin: `http://foo.localhost:${target.server.port}`,
+    });
+  });
+
+  it('rejects requests with non-local Host headers', async () => {
+    const host = `evil.example.com:${target.server.port}`;
+
+    await expect(requestWithHost('/', host)).resolves.toStrictEqual({
+      statusCode: 403,
+    });
+    await expect(
+      requestWithHost(SDK.ServerAPI.API.Manifest, host),
+    ).resolves.toStrictEqual({
+      statusCode: 403,
+    });
+    await expect(
+      requestWithHost('/__open-in-editor?file=/tmp/example.js', host),
+    ).resolves.toStrictEqual({
+      statusCode: 403,
+    });
+  });
+
+  it('supports custom server.cors options', async () => {
+    await expect(
+      optionsWithOrigin(customCorsTarget, 'https://example.com'),
+    ).resolves.toStrictEqual({
+      statusCode: 204,
+      allowOrigin: 'https://example.com',
+    });
+
+    await expect(
+      optionsWithOrigin(
+        customCorsTarget,
+        `http://127.0.0.1:${customCorsTarget.server.port}`,
+      ),
+    ).resolves.toStrictEqual({
+      statusCode: 204,
+      allowOrigin: 'https://example.com',
+    });
+  });
+
+  it('preserves default CORS origins for partial server.cors options', async () => {
+    await expect(
+      optionsWithOrigin(partialCorsTarget, 'https://example.com'),
+    ).resolves.toStrictEqual({
+      statusCode: 403,
+      allowOrigin: undefined,
+    });
+
+    await expect(
+      optionsWithOrigin(
+        partialCorsTarget,
+        `http://127.0.0.1:${partialCorsTarget.server.port}`,
+      ),
+    ).resolves.toStrictEqual({
+      statusCode: 204,
+      allowOrigin: `http://127.0.0.1:${partialCorsTarget.server.port}`,
+    });
+  });
+
   it(`test api: ${SDK.ServerAPI.API.Manifest}`, async () => {
     target.sdk.addClientRoutes([Manifest.RsdoctorManifestClientRoutes.Loaders]);
 
diff --git a/packages/sdk/tests/server/security.test.ts b/packages/sdk/tests/server/security.test.ts
new file mode 100644
index 0000000000000000000000000000000000000000..8a7e95ce2fb7e0b614ce2c32d52f22e0f07236ac
--- /dev/null
+++ b/packages/sdk/tests/server/security.test.ts
@@ -0,0 +1,55 @@
+import { describe, expect, it } from '@rstest/core';
+import {
+  isAllowedCorsRequest,
+  isAllowedRequestHost,
+  isAllowedRequestOrigin,
+} from '../../src/sdk/server/security';
+
+describe('test server/security.ts', () => {
+  it('allows local request origins', () => {
+    expect(isAllowedRequestOrigin(undefined)).toBe(true);
+    expect(isAllowedRequestOrigin('http://localhost:3000')).toBe(true);
+    expect(isAllowedRequestOrigin('https://foo.localhost:3000')).toBe(true);
+    expect(isAllowedRequestOrigin('http://127.0.0.1:3000')).toBe(true);
+    expect(isAllowedRequestOrigin('http://[::1]:3000')).toBe(true);
+  });
+
+  it('rejects non-local request origins', () => {
+    expect(isAllowedRequestOrigin('https://example.com')).toBe(false);
+    expect(isAllowedRequestOrigin('http://foo.localhost.evil.com')).toBe(false);
+    expect(isAllowedRequestOrigin(['http://localhost:3000'])).toBe(false);
+  });
+
+  it('allows local request hosts', () => {
+    expect(isAllowedRequestHost('localhost:3000')).toBe(true);
+    expect(isAllowedRequestHost('foo.localhost:3000')).toBe(true);
+    expect(isAllowedRequestHost('127.0.0.1:3000')).toBe(true);
+    expect(isAllowedRequestHost('[::1]:3000')).toBe(true);
+    expect(isAllowedRequestHost('192.168.1.10:3000')).toBe(true);
+  });
+
+  it('rejects non-local request hosts', () => {
+    expect(isAllowedRequestHost(undefined)).toBe(false);
+    expect(isAllowedRequestHost('example.com:3000')).toBe(false);
+    expect(isAllowedRequestHost('foo.localhost.evil.com:3000')).toBe(false);
+    expect(isAllowedRequestHost(['localhost:3000'])).toBe(false);
+  });
+
+  it('allows CORS requests from matching local origins', () => {
+    expect(
+      isAllowedCorsRequest('http://127.0.0.1:3001', '127.0.0.1:3000'),
+    ).toBe(true);
+    expect(
+      isAllowedCorsRequest('http://foo.localhost:3001', 'foo.localhost:3000'),
+    ).toBe(true);
+  });
+
+  it('rejects CORS requests from non-local or mismatched origins', () => {
+    expect(isAllowedCorsRequest('https://example.com', '127.0.0.1:3000')).toBe(
+      false,
+    );
+    expect(
+      isAllowedCorsRequest('http://foo.localhost:3001', '127.0.0.1:3000'),
+    ).toBe(false);
+  });
+});
diff --git a/packages/sdk/tests/server/socket.test.ts b/packages/sdk/tests/server/socket.test.ts
new file mode 100644
index 0000000000000000000000000000000000000000..28144d502b292c42932e30d8478b6deb8547e39c
--- /dev/null
+++ b/packages/sdk/tests/server/socket.test.ts
@@ -0,0 +1,81 @@
+import { describe, it, expect, rs } from '@rstest/core';
+import { request } from 'http';
+import { setupSDK, type MockSDKResponse } from '../utils';
+
+rs.setConfig({ testTimeout: 50000 });
+
+describe('test server/socket.ts', () => {
+  const target = setupSDK();
+
+  function requestSocketHandshake(
+    target: MockSDKResponse,
+    host?: string,
+    token = target.server.socketUrl.token,
+  ) {
+    return new Promise<{ statusCode: number }>((resolve, reject) => {
+      const url = new URL(target.server.socketUrl.socketUrl);
+      if (token) {
+        url.searchParams.set('token', token);
+      } else {
+        url.searchParams.delete('token');
+      }
+
+      const req = request({
+        hostname: '127.0.0.1',
+        port: target.server.port,
+        path: `${url.pathname}${url.search}`,
+        method: 'GET',
+        headers: {
+          Connection: 'Upgrade',
+          Upgrade: 'websocket',
+          'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
+          'Sec-WebSocket-Version': '13',
+          ...(host ? { Host: host } : {}),
+        },
+      });
+
+      req.on('upgrade', (res, socket) => {
+        socket.destroy();
+        resolve({ statusCode: res.statusCode || 0 });
+      });
+      req.on('response', (res) => {
+        res.resume();
+        res.on('end', () => {
+          resolve({ statusCode: res.statusCode || 0 });
+        });
+      });
+      req.on('error', reject);
+      req.end();
+    });
+  }
+
+  it('rejects socket handshakes without tokens', async () => {
+    await expect(
+      requestSocketHandshake(target, undefined, ''),
+    ).resolves.toStrictEqual({
+      statusCode: 401,
+    });
+  });
+
+  it('allows socket handshakes with valid tokens', async () => {
+    await expect(requestSocketHandshake(target)).resolves.toStrictEqual({
+      statusCode: 101,
+    });
+  });
+
+  it('rejects socket handshakes with non-local Host headers', async () => {
+    await expect(
+      requestSocketHandshake(target, `evil.example.com:${target.server.port}`),
+    ).resolves.toStrictEqual({
+      statusCode: 401,
+    });
+  });
+
+  it('rejects socket handshakes with invalid tokens', async () => {
+    await expect(
+      requestSocketHandshake(target, undefined, 'invalid-token'),
+    ).resolves.toStrictEqual({
+      statusCode: 401,
+    });
+  });
+});
diff --git a/packages/sdk/tests/utils.ts b/packages/sdk/tests/utils.ts
index e9d38d5b2ff98be9077b761c6e853893e83d209c..dcef9dfc56db3c34babe752f92fd5eb3b6848099 100644
--- a/packages/sdk/tests/utils.ts
+++ b/packages/sdk/tests/utils.ts
@@ -38,7 +38,17 @@ export async function createSDK(
   config?: SDK.SDKOptionsType,
 ): Promise<MockSDKResponse> {
   const port = await Server.getPort(getPreferredTestPort());
-  const sdk = new RsdoctorSDK({ name: 'test', root: cwd, port, config });
+  const sdk = new RsdoctorSDK({
+    name: 'test',
+    root: cwd,
+    config: {
+      ...config,
+      server: {
+        ...config?.server,
+        port: config?.server?.port ?? port,
+      },
+    },
+  });
 
   await sdk.bootstrap();
 
diff --git a/packages/types/src/plugin/plugin.ts b/packages/types/src/plugin/plugin.ts
index 14138a2b15d1e2a98d549bf61bf9d3d44d21b680..bd306bc3239fbca4b1b0808f1d3f49ed0473210c 100644
--- a/packages/types/src/plugin/plugin.ts
+++ b/packages/types/src/plugin/plugin.ts
@@ -39,7 +39,14 @@ export interface RsdoctorPluginOptionsNormalized<
 > extends Common.DeepRequired<
   Omit<
     RsdoctorRspackPluginOptions<Rules>,
-    'sdkInstance' | 'linter' | 'output' | 'supports' | 'port' | 'brief' | 'mode'
+    | 'sdkInstance'
+    | 'linter'
+    | 'output'
+    | 'supports'
+    | 'port'
+    | 'brief'
+    | 'mode'
+    | 'server'
   >
 > {
   features: Common.DeepRequired<RsdoctorRspackPluginFeatures>;
@@ -52,6 +59,7 @@ export interface RsdoctorPluginOptionsNormalized<
     options: Config.BriefModeOptions | Config.NormalModeOptions;
   };
   port?: number;
+  server: SDK.RsdoctorServerConfig;
   supports: ISupport;
 }
 
@@ -139,9 +147,16 @@ export interface RsdoctorRspackPluginOptions<
 
   /**
    * The port of the Rsdoctor server.
+   *
+   * @deprecated Use `server.port` instead.
    */
   port?: number;
 
+  /**
+   * Options for the Rsdoctor report server.
+   */
+  server?: SDK.RsdoctorServerConfig;
+
   /**
    * Options to control the log printing.
    */
diff --git a/packages/types/src/sdk/instance.ts b/packages/types/src/sdk/instance.ts
index 512899f2c451fa9c2b3c97c9ec151ecca65350fe..dca25083f364f1430cf708a277ca380fcc3c3ed1 100644
--- a/packages/types/src/sdk/instance.ts
+++ b/packages/types/src/sdk/instance.ts
@@ -122,6 +122,50 @@ export interface IPrintLog {
   serverUrls: boolean;
 }
 
+export type RsdoctorServerCorsStaticOrigin =
+  | boolean
+  | string
+  | RegExp
+  | Array<boolean | string | RegExp>;
+
+export type RsdoctorServerCorsOrigin =
+  | RsdoctorServerCorsStaticOrigin
+  | ((
+      requestOrigin: string | undefined,
+      callback: (
+        err: Error | null,
+        origin?: RsdoctorServerCorsStaticOrigin,
+      ) => void,
+    ) => void);
+
+export interface RsdoctorServerCorsOptions {
+  origin?: RsdoctorServerCorsOrigin;
+  methods?: string | string[];
+  allowedHeaders?: string | string[];
+  exposedHeaders?: string | string[];
+  credentials?: boolean;
+  maxAge?: number;
+  preflightContinue?: boolean;
+  optionsSuccessStatus?: number;
+}
+
+export interface RsdoctorServerConfig {
+  /**
+   * The port of the Rsdoctor report server.
+   */
+  port?: number;
+  /**
+   * Configure CORS for the Rsdoctor report server.
+   *
+   * - `false`: disable CORS middleware
+   * - `true`: use the cors middleware defaults
+   * - object: pass options to the cors middleware
+   *
+   * By default, Rsdoctor only allows local origins.
+   */
+  cors?: boolean | RsdoctorServerCorsOptions;
+}
+
 export type SDKOptionsType = {
   innerClientPath?: string;
   disableClientServer?: boolean;
@@ -130,4 +174,5 @@ export type SDKOptionsType = {
   mode?: keyof typeof IMode;
   brief?: BriefModeOptions;
   features?: { treeShaking?: boolean };
+  server?: RsdoctorServerConfig;
 };
diff --git a/packages/types/src/sdk/server/index.ts b/packages/types/src/sdk/server/index.ts
index af1d6e913e182865d953cd5082d680fbcde10846..88230255b900b888093d87f2e69e6d249f63f101 100644
--- a/packages/types/src/sdk/server/index.ts
+++ b/packages/types/src/sdk/server/index.ts
@@ -19,6 +19,11 @@ export interface RsdoctorServerInstance {
 
   readonly port: number;
   readonly origin: string;
+  readonly socketUrl: {
+    port: number;
+    socketUrl: string;
+    token: string;
+  };
 
   innerClientPath?: string;
 
diff --git a/packages/utils/src/common/global-config.ts b/packages/utils/src/common/global-config.ts
index 8bb75c86b63cdd40ae7149a702f39bd3ffe2becf..b881da08a7ccee12fbc14542829505318d4db138 100644
--- a/packages/utils/src/common/global-config.ts
+++ b/packages/utils/src/common/global-config.ts
@@ -12,7 +12,7 @@ import { logger } from '../logger';
  *     builder1: portNumber,
  *     builder2: portNumber,
  *   },
- *   port: portNumber // The port of the last builder is used by default
+ *   port: portNumber, // The port of the last builder is used by default
  * }
  *
  * @param {number} port - The port number to write.
@@ -27,7 +27,10 @@ export function writeMcpPort(port: number, builderName?: string) {
     fs.mkdirSync(rsdoctorDir, { recursive: true });
   }
 
-  let mcpJson: { portList: Record<string, number>; port: number } = {
+  let mcpJson: {
+    portList: Record<string, number>;
+    port: number;
+  } = {
     portList: {},
     port: 0,
   };
diff --git a/packages/utils/tests/server.test.ts b/packages/utils/tests/server.test.ts
index 951ce9ab7772ca4ad415a69ad0bfe70160094acc..303188f554c29eb59d9c93357eb227fbfb54270e 100644
--- a/packages/utils/tests/server.test.ts
+++ b/packages/utils/tests/server.test.ts
@@ -1,6 +1,11 @@
 import { describe, it, expect } from '@rstest/core';
+import type { AddressInfo } from 'net';
 import { Server } from '../src/build';
-import { getPortSync } from '../src/build/server';
+import {
+  createGetPortSyncFunctionString,
+  defaultHost,
+  getPortSync,
+} from '../src/build/server';
 
 describe('test src/server.ts', () => {
   it('getPort()', async () => {
@@ -18,4 +23,31 @@ describe('test src/server.ts', () => {
     expect(getPortSync(8262)).not.toEqual(8262);
     await close();
   });
+
+  it('binds to 127.0.0.1 by default', async () => {
+    const { server, close } = await Server.createServer(0);
+
+    try {
+      const address = server.address() as AddressInfo;
+      expect(address.address).toEqual(defaultHost);
+      expect(createGetPortSyncFunctionString(3543)).toContain(
+        `getPort(port, ${JSON.stringify(defaultHost)})`,
+      );
+    } finally {
+      await close();
+    }
+  });
+
+  it('rejects when the requested port is already in use', async () => {
+    const { server, close } = await Server.createServer(0);
+    const { port } = server.address() as AddressInfo;
+
+    try {
+      await expect(Server.createServer(port)).rejects.toMatchObject({
+        code: 'EADDRINUSE',
+      });
+    } finally {
+      await close();
+    }
+  });
 });

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### packages/cli/src/commands/analyze.ts
```
import { Manifest } from '@rsdoctor/utils/common';
import { Constants, Manifest as ManifestType, SDK } from '@rsdoctor/types';
import { RsdoctorSDK } from '@rsdoctor/sdk';
import ora from 'ora';
import { cyan, red } from 'picocolors';
import { Command } from '../types';
import {
  enhanceCommand,
  loadJSON,
  loadShardingFileWithSpinner,
} from '../utils';
import { Commands } from '../constants';

interface Options {
  profile: string;
  open?: boolean;
  port?: number;
  type?: SDK.ToDataType;
}

export const analyze: Command<Commands.Analyze, Options, RsdoctorSDK> =
  enhanceCommand(({ cwd, name, bin }) => ({
    command: Commands.Analyze,
    description: `
use ${name} to open "${Constants.RsdoctorOutputManifestPath}" in browser for analysis.

example: ${bin} ${Commands.Analyze} --profile "${Constants.RsdoctorOutputManifestPath}"

`.trim(),
    options(cli) {
      cli
        .option('--profile <path>', 'profile for Rsdoctor server')
        .option(
          '--no-open',
          'turn off it if you need not open browser automatically',
        )
        .option('--port <number>', 'port for Rsdoctor Server');
    },
    async action({ profile, open = true, port, type = SDK.ToDataType.Normal }) {
      const spinner = ora({ prefixText: cyan(`[${name}]`) }).start(
        `start to loading "${profile}"`,
      );

      const json =
        await loadJSON<ManifestType.RsdoctorManifestWithShardingFiles>(
          profile,
          cwd,
        );

      spinner.text = `start to loading data...`;

      let dataValue: ManifestType.RsdoctorManifestData;

      try {
        dataValue = await Manifest.fetchShardingFiles(
          json.data,
          (url: string) => loadShardingFileWithSpinner(url, cwd, spinner),
        );
      } catch (error) {
        try {
          dataValue = await Manifest.fetchShardingFiles(
            json.cloudData || {},
            (url: string) => loadShardingFileWithSpinner(url, cwd, spinner),
          );
        } catch {
          spinner.fail(red((error as Error).message));
          throw error;
        }
      }

      spinner.text = `start server`;

      const sdk = new RsdoctorSDK({ name, root: cwd, port, type });

      await sdk.bootstrap();

      sdk.getStoreData = () => dataValue;
      sdk.getManifestData = () => json;

      const manifestBuffer = Buffer.from(
        JSON.stringify({ ...json, __LOCAL__SERVER__: true }),
      );

      sdk.server.proxy(SDK.ServerAPI.API.Manifest, 'GET', () => manifestBuffer);

      if (open) {
        spinner.succeed(`open browser automatically`);

        await sdk.server.openClientPage('homepage');
      }

      spinner.succeed(
        `the local url: ${cyan(sdk.server.getClientUrl('homepage'))}`,
      );

      return sdk;
    },
  }));

```

### packages/cli/src/commands/stats-analyze.ts
```
import { RsdoctorSDK } from '@rsdoctor/sdk';
import { Constants, Manifest as ManifestType, SDK } from '@rsdoctor/types';
import { cyan } from 'picocolors';
import ora from 'ora';
import { Commands } from '../constants';
import { Command } from '../types';
import { enhanceCommand, readFile } from '../utils';
import type { Plugin } from '@rsdoctor/types';
import { TransUtils } from '@rsdoctor/graph';

interface Options {
  profile: string;
  open?: boolean;
  port?: number;
  type?: SDK.ToDataType;
}

export const statsAnalyze: Command<
  Commands.StatsAnalyze,
  Options,
  RsdoctorSDK
> = enhanceCommand(({ cwd, name, bin }) => ({
  command: Commands.StatsAnalyze,
  description:
    `use ${name} to open "${Constants.RsdoctorOutputManifestPath}" in browser for analysis.example: ${bin} ${Commands.StatsAnalyze} --profile "${Constants.StatsFilePath}"`.trim(),
  options(cli) {
    cli
      .option(
        '--profile <path>',
        'Path to webpack stats.json file for analysis',
      )
      .option('--port <number>', 'port for Rsdoctor Server')
      .option('--type <mode>', 'Bundle analysis mode (normal or lite)');
  },
  async action({ profile, open = true, type = SDK.ToDataType.Normal }) {
    const spinner = ora({ prefixText: cyan(`[${name}]`) }).start(
      `start to loading "${profile}"`,
    );
    const statsStrings = await readFile(profile, cwd);
    const json = JSON.parse(statsStrings) as Plugin.StatsCompilation;

    spinner.text = `start server`;
    const { chunkGraph, moduleGraph } = await TransUtils.transStats(json);

    const sdk = new RsdoctorSDK({
      name: 'stats-analyze',
      root: process.cwd(),
      type,
      noServer: false,
    });

    await sdk.bootstrap();
    sdk.reportChunkGraph(chunkGraph);
    sdk.reportModuleGraph(moduleGraph);
    sdk.addClientRoutes([
      ManifestType.RsdoctorManifestClientRoutes.Overall,
      ManifestType.RsdoctorManifestClientRoutes.BundleSize,
      ManifestType.RsdoctorManifestClientRoutes.ModuleGraph,
    ]);

    if (open) {
      spinner.succeed(`open browser automatically`);

      await sdk.server.openClientPage('homepage');
    }

    spinner.succeed(
      `the local url: ${cyan(sdk.server.getClientUrl('homepage'))}`,
    );

    return sdk;
  },
}));

```

### packages/components/src/utils/data/local.ts
```
import { Manifest as ManifestShared } from '@rsdoctor/utils/common';
import { Common, Manifest, SDK } from '@rsdoctor/types';
import { get } from '@rsdoctor/utils/collection';
import { BaseDataLoader } from './base';
import { postServerAPI } from '../request';
import {
  requestServerAPI,
  subscribeServerAPI,
  unsubscribeServerAPI,
} from '../socket';

type DataUpdateAPI = SDK.ServerAPI.API | SDK.ServerAPI.APIExtends;

type DataUpdateSubscription = {
  api: DataUpdateAPI;
  body: SDK.ServerAPI.InferRequestBodyType<DataUpdateAPI, null> | null;
  listeners: Set<Common.Function>;
};

export class LocalServerDataLoader extends BaseDataLoader {
  protected events: Map<string, DataUpdateSubscription> = new Map();

  public isLocal() {
    return true;
  }

  public async loadData<T extends keyof Manifest.RsdoctorManifestData>(
    key: T,
  ): Promise<void | Manifest.RsdoctorManifestData[T]>;

  public async loadData(key: string): Promise<unknown> {
    return this.limit(key, async () => {
      const [scope, ...rest] = this.getKeys(key);
      const data = this.getData(scope as keyof Manifest.RsdoctorManifestData);

      if (!data) return;

      let res: unknown = data;

      // sharding files
      if (ManifestShared.isShardingData(res)) {
        if (!this.shardingDataMap.has(key)) {
          const task = postServerAPI(SDK.ServerAPI.API.LoadDataByKey, {
            key,
          }).catch((err) => {
            this.log(`loadData error: `, res, key);
            throw err;
          });
          // save with every key
          this.shardingDataMap.set(key, task);
        }

        res = await this.shardingDataMap.get(key);
        this.shardingDataMap.delete(key);
        return res;
      }

      return rest.length > 0 ? get(res, this.joinKeys(rest)) : res;
    });
  }

  public async loadAPI<
    T extends SDK.ServerAPI.API,
    B extends SDK.ServerAPI.InferRequestBodyType<T> =
      SDK.ServerAPI.InferRequestBodyType<T>,
    R extends SDK.ServerAPI.InferResponseType<T> =
      SDK.ServerAPI.InferResponseType<T>,
  >(...args: B extends void ? [api: T] : [api: T, body: B]): Promise<R> {
    const [api, body] = args;
    // request limitation key
    const key = body ? `${api}_${JSON.stringify(body)}` : `${api}`;
    const socketPort = this.get('__SOCKET__PORT__') ?? '';

    return this.limit(key, async () => {
      try {
        return (await requestServerAPI(
          api,
          body as SDK.ServerAPI.InferRequestBodyType<T>,
          socketPort,
        )) as R;
      } catch (err) {
        this.log(`loadAPI error: `, key);
        throw err;
      }
    });
  }

  public dispose() {
    super.dispose();
    this.events.forEach(({ api, body, listeners }) => {
      listeners.forEach((listener) => {
        this.removeOnDataUpdate(api, body, listener);
      });
      listeners.clear();
    });
    this.events.clear();
  }

  /**
   * add event listener when received data from server.
   */
  public onDataUpdate<T extends SDK.ServerAPI.API | SDK.ServerAPI.APIExtends>(
    api: T,
    body: SDK.ServerAPI.InferRequestBodyType<T, null> | null,
    fn: (response: SDK.ServerAPI.SocketResponseType<T>) => void,
  ) {
    const normalizedBody = body ?? null;
    const key = `${api}::${JSON.stringify(normalizedBody)}`;
    if (!this.events.has(key)) {
      this.events.set(key, {
        api,
        body: normalizedBody,
        listeners: new Set(),
      });
    }

    const subscription = this.events.get(key)!;
    if (subscription.listeners.has(fn)) {
      return;
    }

    subscription.listeners.add(fn);
    const socketPort = this.get('__SOCKET__PORT__') ?? '';
    subscribeServerAPI(api, normalizedBody, fn, socketPort);
  }

  public removeOnDataUpdate<
    T extends SDK.ServerAPI.API | SDK.ServerAPI.APIExtends,
  >(
    api: T,
    body: SDK.ServerAPI.InferRequestBodyType<T, null> | null,
    fn: (response: SDK.ServerAPI.SocketResponseType<T>) => void,
  ) {
    const key = `${api}::${JSON.stringify(body ?? null)}`;
    const socketPort = this.get('__SOCKET__PORT__') ?? '';
    unsubscribeServerAPI(api, body, fn, socketPort);
    this.events.get(key)?.listeners.delete(fn);
  }
}

```

### packages/components/src/utils/socket.ts
```
/* rslint-disable no-restricted-globals */
import type { Common, SDK } from '@rsdoctor/types';

type SocketAPI = SDK.ServerAPI.API | SDK.ServerAPI.APIExtends;

export interface ServerSocketMessage<T extends SocketAPI = SocketAPI> {
  api: T;
  payload: SDK.ServerAPI.SocketResponseType<T>;
}

type ServerSocketResponseMessage<
  T extends SDK.ServerAPI.API = SDK.ServerAPI.API,
> = {
  type: 'response';
  id: string;
  payload?: SDK.ServerAPI.InferResponseType<T>;
  error?: string;
};

type SocketListener<T extends SocketAPI = SocketAPI> = (
  payload: SDK.ServerAPI.SocketResponseType<T>,
) => void;

type Subscription = {
  api: SocketAPI;
  body: Common.PlainObject | null | undefined;
};

type PendingRequest = {
  message: string;
  resolve: (payload: unknown) => void;
  reject: (error: Error) => void;
};

type SocketClient = {
  url: string;
  socket?: WebSocket;
  listeners: Map<string, Set<SocketListener>>;
  subscriptions: Map<string, Subscription>;
  requests: Map<string, PendingRequest>;
};

const clients = new Map<string, SocketClient>();
const defaultClientKey = '__default__';
const openState = 1;
let requestId = 0;

const ipv4Pattern =
  /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

function getSocketProtocol(protocol: string) {
  return protocol.includes('https') ? 'wss' : 'ws';
}

function getDefaultSocketUrl() {
  if (typeof location === 'undefined') {
    return '';
  }

  const socketProtocol = getSocketProtocol(location.protocol);
  return process.env.NODE_ENV === 'development'
    ? `${socketProtocol}://${location.hostname}:${process.env.LOCAL_CLI_PORT}`
    : `${socketProtocol}://${location.host}`;
}

function getSocketUrl(socketPort?: string) {
  if (typeof location === 'undefined') {
    return socketPort ? `ws://localhost:${socketPort}` : '';
  }

  return socketPort
    ? formatURL({
        port: socketPort,
        hostname: location.hostname,
        protocol: location.protocol,
      })
    : getDefaultSocketUrl();
}

function getClient(socketUrl = getDefaultSocketUrl()) {
  const key = socketUrl || defaultClientKey;
  if (!clients.has(key)) {
    clients.set(key, {
      url: socketUrl,
      listeners: new Map(),
      subscriptions: new Map(),
      requests: new Map(),
    });
  }
  return clients.get(key)!;
}

function getSubscriptionKey(api: SocketAPI, body: unknown) {
  return `${api}:${JSON.stringify(body ?? null)}`;
}

function sendSubscription(client: SocketClient, subscription: Subscription) {
  if (client.socket?.readyState !== openState) {
    return;
  }

  client.socket.send(
    JSON.stringify({
      type: 'subscribe',
      api: subscription.api,
      body: subscription.body ?? null,
    }),
  );
}

function sendUnsubscribe(client: SocketClient, subscription: Subscription) {
  if (client.socket?.readyState !== openState) {
    return;
  }

  client.socket.send(
    JSON.stringify({
      type: 'unsubscribe',
      api: subscription.api,
      body: subscription.body ?? null,
    }),
  );
}

function sendRequest(client: SocketClient, id: string) {
  if (client.socket?.readyState !== openState) {
    return;
  }

  const request = client.requests.get(id);
  if (!request) {
    return;
  }
  client.socket.send(request.message);
}

function handleResponseMessage(
  client: SocketClient,
  message: ServerSocketResponseMessage,
) {
  const request = client.requests.get(message.id);
  if (!request) {
    return;
  }

  client.requests.delete(message.id);
  if (message.error) {
    request.reject(new Error(message.error));
    return;
  }
  request.resolve(message.payload);
}

function connectSocket(client: SocketClient) {
  if (!client.url || typeof WebSocket === 'undefined' || client.socket) {
    return;
  }

  const socket = new WebSocket(client.url);
  socket.addEventListener('open', () => {
    client.subscriptions.forEach((subscription) => {
      sendSubscription(client, subscription);
    });
    client.requests.forEach((_, id) => {
      sendRequest(client, id);
    });
  });
  socket.addEventListener('message', (event) => {
    if (typeof event.data !== 'string') {
      return;
    }

    try {
      const message = JSON.parse(event.data) as
        | ServerSocketMessage
        | ServerSocketResponseMessage;
      if ('type' in message && message.type === 'response') {
        handleResponseMessage(client, message);
        return;
      }
      publishServerSocketMessage(message as ServerSocketMessage, client.url);
    } catch {
      // Ignore malformed payloads and keep the transport alive.
    }
  });
  socket.addEventListener('close', () => {
    client.socket = undefined;
    client.requests.forEach((request) => {
      request.reject(
        new Error('WebSocket closed before the response arrived.'),
      );
    });
    client.requests.clear();
  });
  client.socket = socket;
}

export function requestServerAPI<
  T extends SDK.ServerAPI.API,
  B extends SDK.ServerAPI.InferRequestBodyType<T> =
    SDK.ServerAPI.InferRequestBodyType<T>,
  R extends SDK.ServerAPI.InferResponseType<T> =
    SDK.ServerAPI.InferResponseType<T>,
>(api: T, body: B | null | undefined, socketPort?: string): Promise<R> {
  const socketUrl = getSocketUrl(socketPort);
  if (!socketUrl) {
    return Promise.reject(new Error('WebSocket URL is not available.'));
  }

  if (typeof WebSocket === 'undefined') {
    return Promise.reject(new Error('WebSocket is not available.'));
  }

  const client = getClient(socketUrl);
  const id = `${Date.now()}-${++requestId}`;

  return new Promise<R>((resolve, reject) => {
    client.requests.set(id, {
      message: JSON.stringify({
        type: 'request',
        id,
        api,
        body: body ?? null,
      }),
      resolve: resolve as (payload: unknown) => void,
      reject,
    });
    connectSocket(client);
    sendRequest(client, id);
  });
}

export function subscribeServerAPI<T extends SocketAPI>(
  api: T,
  body: SDK.ServerAPI.InferRequestBodyType<T, null> | null,
  listener: SocketListener<T>,
  socketPort?: string,
) {
  const client = getClient(getSocketUrl(socketPort));
  const bodyValue = body ?? null;
  const key = getSubscriptionKey(api, bodyValue);
  if (!client.listeners.has(key)) {
    client.listeners.set(key, new Set());
  }
  client.listeners.get(key)!.add(listener as SocketListener);

  const subscription = {
    api,
    body: bodyValue,
  };
  client.subscriptions.set(key, subscription);
  connectSocket(client);
  sendSubscription(client, subscription);

  return () => {
    unsubscribeServerAPI(api, bodyValue, listener, socketPort);
  };
}

export function unsubscribeServerAPI<T extends SocketAPI>(
  api: T,
  body: SDK.ServerAPI.InferRequestBodyType<T, null> | null,
  listener: SocketListener<T>,
  socketPort?: string,
) {
  const client = getClient(getSocketUrl(socketPort));
  const key = getSubscriptionKey(api, body);
  const listeners = client.listeners.get(key);
  listeners?.delete(listener as SocketListener);

  if (listeners?.size === 0) {
    const subscription = client.subscriptions.get(key);
    if (subscription) {
      sendUnsubscribe(client, subscription);
    }
    client.listeners.delete(key);
    client.subscriptions.delete(key);
  }
}

export function publishServerSocketMessage(
  message: ServerSocketMessage,
  socketUrl?: string,
) {
  const targets = socketUrl ? [getClient(socketUrl)] : [...clients.values()];

  targets.forEach((client) => {
    const key = getSubscriptionKey(message.api, message.payload.req.body);
    client.listeners.get(key)?.forEach((listener) => {
      listener(message.payload);
    });
  });
}

export function formatURL({
  port,
  protocol,
  hostname,
}: {
  port?: string;
  protocol: string;
  hostname: string;
}) {
  const socketProtocol = getSocketProtocol(protocol);
  const shouldUsePort =
    ipv4Pattern.test(hostname) || hostname.includes('localhost');

  if (typeof URL !== 'undefined') {
    const url = new URL('http://localhost');
    url.hostname = hostname;
    url.protocol = socketProtocol;
    if (port && shouldUsePort) {
      url.port = port;
    }
    return url.toString();
  }

  const portText = port && shouldUsePort ? `:${port}` : '';
  return `${socketProtocol}://${hostname}${portText}`;
}

```

### packages/core/src/inner-plugins/utils/config.ts
```
import {
  RsdoctorRspackPluginOptions,
  RsdoctorRspackPluginOptionsNormalized,
} from '@/types';
import { Config, Linter, Plugin, SDK } from '@rsdoctor/types';
import { chalk, logger } from '@rsdoctor/utils/logger';
import assert from 'assert';
import {
  convertReportCodeTypeObject,
  processModeConfigurations,
} from './normalize-config';

function defaultBoolean(v: unknown, dft: boolean): boolean {
  return typeof v === 'boolean' ? v : dft;
}
function getDefaultOutput() {
  return {
    mode: undefined,
    reportCodeType: {
      noModuleSource: false,
      noAssetsAndModuleSource: false,
      noCode: false,
    },
    options: undefined,
    reportDir: '',
    compressData: undefined,
  };
}
function getDefaultSupports() {
  return {
    parseBundle: true,
    gzip: true, // change the gzip to true by default.
  };
}
function isJsonOutputEnv(value: unknown): boolean {
  return value === 'json';
}
function normalizeFeatures(features: any, mode: keyof typeof SDK.IMode) {
  if (Array.isArray(features)) {
    return {
      loader: features.includes('loader'),
      plugins: features.includes('plugins'),
      resolver: features.includes('resolver'),
      bundle: features.includes('bundle'),
      treeShaking: features.includes('treeShaking'),
      lite: features.includes('lite') || mode === SDK.IMode[SDK.IMode.lite],
    };
  }
  return {
    loader: defaultBoolean(features.loader, true),
    plugins: defaultBoolean(features.plugins, true),
    resolver: defaultBoolean(features.resolver, false),
    bundle: defaultBoolean(features.bundle, true),
    treeShaking: defaultBoolean(features.treeShaking, false),
    lite:
      defaultBoolean(features.lite, false) ||
      mode === SDK.IMode[SDK.IMode.lite],
  };
}
function normalizeLinter(linter: any) {
  return {
    rules: {} as any,
    extends: [] as any,
    level: 'Error',
    ...linter,
  };
}

function isValidMode(mode: any): mode is keyof typeof SDK.IMode {
  return typeof mode === 'string' && ['brief', 'normal', 'lite'].includes(mode);
}

export function normalizeUserConfig<Rules extends Linter.ExtendRuleData[]>(
  config: Plugin.RsdoctorRspackPluginOptions<Rules> = {},
): Plugin.RsdoctorPluginOptionsNormalized<Rules> {
  const userOutput = config.output;
  const defaultOutput = getDefaultOutput();
  const outputConfig: Config.IOutput<'brief' | 'normal'> = isJsonOutputEnv(
    process.env.RSDOCTOR_OUTPUT,
  )
    ? {
        reportDir: userOutput?.reportDir,
        compressData: userOutput?.compressData,
        mode: 'brief' as const,
        options: {
          type: ['json'] as Array<'json'>,
        },
      }
    : (userOutput ?? defaultOutput);
  const normalizedConfig = {
    ...config,
    output: outputConfig,
  };
  const {
    linter = {},
    features = {},
    loaderInterceptorOptions = {},
    disableClientServer: userDisableClientServer = false,
    sdkInstance,
    innerClientPath = '',
    output = outputConfig,
    supports = getDefaultSupports(),
    port,
    printLog = { serverUrls: true },
    mode = undefined,
    brief = undefined,
  } = normalizedConfig;
  // If process.env.RSTEST is set to true, disableClientServer should be false
  // Otherwise, if process.env.CI is set, disableClientServer should be true
  const disableClientServer =
    process.env.RSTEST === 'true'
      ? false
      : process.env.CI
        ? true
        : userDisableClientServer;
  assert(typeof linter === 'object');
  assert(typeof features === 'object' || Array.isArray(features));
  assert(typeof loaderInterceptorOptions === 'object');
  assert(typeof disableClientServer === 'boolean');
  let finalMode: keyof typeof SDK.IMode =
    ('mode' in output && isValidMode(output.mode)
      ? output.mode === ('lite' as SDK.IMode.normal)
        ? SDK.IMode[SDK.IMode.normal]
        : output.mode
      : undefined) ||
    mode ||
    SDK.IMode[SDK.IMode.normal];

  if (mode) {
    logger.info(
      chalk.yellow(
        `The 'mode' configuration will be deprecated in a future version. Please use 'output.mode' instead.`,
      ),
    );
  }
  const _features = normalizeFeatures(features, finalMode);
  const _linter = normalizeLinter(linter);
  if (_features.lite || finalMode === SDK.IMode[SDK.IMode.lite]) {
    logger.info(
      chalk.yellow(
        `Lite features will be deprecated in a future version. Please use 'output: { reportCodeType: { noAssetsAndModuleSource: true }}' instead.`,
      ),
    );
  }
  // Process mode-specific configurations
  const { finalBrief, finalNormalOptions } = processModeConfigurations(
    finalMode,
    output,
    brief,
  );
  // If lite mode is enabled and mode is not brief: finalBrief, set mode to lite
  if (_features.lite && finalMode !== SDK.IMode[SDK.IMode.brief]) {
    finalMode = SDK.IMode[SDK.IMode.lite] as keyof typeof SDK.IMode;
  }
  const reportCodeType = output.reportCodeType
    ? normalizeReportType(output.reportCodeType, finalMode)
    : normalizeReportType(getDefaultOutput().reportCodeType, finalMode);
  const res: Plugin.RsdoctorPluginOptionsNormalized<Rules> = {
    linter: _linter,
    features: _features,
    loaderInterceptorOptions: {
      skipLoaders: Array.isArray(loaderInterceptorOptions.skipLoaders)
        ? loaderInterceptorOptions.skipLoaders
        : [],
    },
    disableClientServer,
    sdkInstance,
    output: {
      mode: finalMode,
      options: finalMode === 'brief' ? finalBrief : finalNormalOptions,
      reportCodeType,
      reportDir: output.reportDir || '',
    },
    innerClientPath,
    supports,
    port,
    printLog,
  };

  // Add deprecation warning for compressData
  if (output.compressData !== undefined) {
    logger.info(
      chalk.yellow(
        `The 'compressData' configuration will be deprecated in a future version.`,
      ),
    );
  }

  return res;
}

export const normalizeReportType = (
  reportCodeType: Plugin.IReportCodeType | Plugin.NewReportCodeType,
  mode: keyof typeof SDK.IMode,
): SDK.ToDataType => {
  const convertedReportCodeType =
    typeof reportCodeType === 'object'
      ? convertReportCodeTypeObject(reportCodeType)
      : reportCodeType;
  if (convertedReportCodeType === 'noCode') {
    return SDK.ToDataType.NoCode;
  }
  if (mode === SDK.IMode[SDK.IMode.brief]) {
    return SDK.ToDataType.NoCode;
  }
  if (mode === SDK.IMode[SDK.IMode.lite]) {
    return SDK.ToDataType.NoSourceAndAssets;
  }
  if (convertedReportCodeType === 'noAssetsAndModuleSource') {
    return SDK.ToDataType.NoSourceAndAssets;
  }
  if (convertedReportCodeType === 'noModuleSource') {
    return SDK.ToDataType.NoSource;
  }
  return SDK.ToDataType.Normal;
};

export function normalizeRspackUserOptions<
  Rules extends Linter.ExtendRuleData[],
>(
  options: RsdoctorRspackPluginOptions<Rules>,
): RsdoctorRspackPluginOptionsNormalized<Rules> {
  const config: RsdoctorRspackPluginOptionsNormalized<Rules> =
    normalizeUserConfig(options);
  config.experiments ??= {
    enableNativePlugin: {
      moduleGraph: true,
      chunkGraph: true,
    },
  };
  // Default to true, only set to false when explicitly set to false
  if (
    typeof options.experiments?.enableNativePlugin === 'boolean' &&
    options.experiments?.enableNativePlugin === false
  ) {
    config.experiments.enableNativePlugin = {
      moduleGraph: false,
      chunkGraph: false,
    };
  }
  return config;
}

```

### packages/rspack-plugin/src/multiple.ts
```
import type { RsdoctorMultiplePluginOptions } from '@rsdoctor/core/types';
import { RsdoctorPrimarySDK, RsdoctorSDKController } from '@rsdoctor/sdk';
import { SDK, type Linter } from '@rsdoctor/types';

import { normalizeUserConfig } from '@rsdoctor/core/plugins';
import type { Compiler } from '@rspack/core';
import { RsdoctorRspackPlugin } from './plugin';

let globalController: RsdoctorSDKController | undefined;

export class RsdoctorRspackMultiplePlugin<
  Rules extends Linter.ExtendRuleData[],
> extends RsdoctorRspackPlugin<Rules> {
  // @ts-expect-error
  private controller: RsdoctorSDKController;

  constructor(options: RsdoctorMultiplePluginOptions<Rules> = {}) {
    const controller = (() => {
      if (globalController) {
        return globalController;
      }
      const controller = new RsdoctorSDKController();
      globalController = controller;
      return controller;
    })();

    const normallizedOptions = normalizeUserConfig<Rules>(options);

    const instance = controller.createSlave({
      name: options.name || 'Builder',
      stage: options.stage,
      extraConfig: {
        innerClientPath: normallizedOptions.innerClientPath,
        printLog: normallizedOptions.printLog,
        mode: normallizedOptions.output.mode
          ? normallizedOptions.output.mode
          : undefined,
        brief:
          normallizedOptions.output.mode === SDK.IMode[SDK.IMode.brief]
            ? normallizedOptions.output.options || undefined
            : undefined,
      },
      type: normallizedOptions.output.reportCodeType,
    });

    super({
      ...options,
      sdkInstance: instance,
    });
    this.controller = controller;
  }

  apply(compiler: Compiler) {
    if ('dependencies' in compiler.options) {
      (this.sdk as RsdoctorPrimarySDK).dependencies =
        compiler.options.dependencies;
    }

    super.apply(compiler);
  }
}

```

### packages/rspack-plugin/src/plugin.ts
```
import { Loader as BuildUtilLoader } from '@rsdoctor/core/build-utils';
import {
  ensureModulesChunksGraphFn,
  InternalBundlePlugin,
  InternalErrorReporterPlugin,
  InternalLoaderPlugin,
  InternalPluginsPlugin,
  InternalResolverPlugin,
  InternalRulesPlugin,
  InternalSummaryPlugin,
  normalizeRspackUserOptions,
  setSDK,
} from '@rsdoctor/core/plugins';
import type {
  RsdoctorRspackPluginInstance,
  RsdoctorRspackPluginOptions,
  RsdoctorRspackPluginOptionsNormalized,
} from '@rsdoctor/core/types';
import { findRoot, RsdoctorPrimarySDK, RsdoctorSDK } from '@rsdoctor/sdk';
import {
  Constants,
  Linter,
  Manifest,
  Manifest as ManifestType,
  Plugin,
  SDK,
} from '@rsdoctor/types';
import path from 'path';
import { pluginTapName, pluginTapPostOptions, pkg } from './constants';

import {
  handleBriefModeReport,
  processCompilerConfig,
} from '@rsdoctor/core/plugins';

import { ModuleGraph } from '@rsdoctor/graph';
import { Loader } from '@rsdoctor/utils/common';
import { logger, time, timeEnd } from '@rsdoctor/utils/logger';

// Static flag to ensure greet message is only printed once per process
let hasGreeted = false;

export class RsdoctorRspackPlugin<
  Rules extends Linter.ExtendRuleData[],
> implements RsdoctorRspackPluginInstance<Rules> {
  public readonly name = pluginTapName;

  public readonly sdk: SDK.RsdoctorBuilderSDKInstance | RsdoctorPrimarySDK;

  public readonly isRsdoctorPlugin: boolean;

  public _bootstrapTask!: Promise<unknown>;

  protected browserIsOpened = false;

  public modulesGraph: SDK.ModuleGraphInstance;

  public options: RsdoctorRspackPluginOptionsNormalized<Rules>;

  public outsideInstance: boolean;

  constructor(options?: RsdoctorRspackPluginOptions<Rules>) {
    this.options = normalizeRspackUserOptions<Rules>(
      Object.assign(options || {}, {
        supports: {
          ...options?.supports,
        },
      }),
    );
    const { port, output, innerClientPath, printLog, sdkInstance } =
      this.options;

    this.sdk =
      this.options.sdkInstance ??
      new RsdoctorSDK({
        port,
        name: pluginTapName,
        root: process.cwd(),
        type: output.reportCodeType,
        config: {
          innerClientPath,
          printLog,
          mode: output.mode ? output.mode : undefined,
          brief:
            output.mode === SDK.IMode[SDK.IMode.brief]
              ? output.options || undefined
              : undefined,
          features: { treeShaking: this.options.features.treeShaking },
        },
      });
    this.outsideInstance = Boolean(sdkInstance);
    this.modulesGraph = new ModuleGraph();
    this.isRsdoctorPlugin = true;
  }

  // avoid hint error from ts type validation
  apply(compiler: unknown): unknown;

  apply(compiler: Plugin.BaseCompilerType<'rspack'>) {
    time('RsdoctorRspackPlugin.apply');
    try {
      if (!hasGreeted && !compiler.isChild()) {
        hasGreeted = true;
        logger.greet(`
        \nRsdoctor v${pkg.version}\n`);
      }

      // bootstrap sdk in apply()
      // Avoid creating different sdk instances when config generators recreate plugin instances.
      if (!this._bootstrapTask) {
        this._bootstrapTask = this.sdk.bootstrap();
      }

      if (compiler.options.name) {
        this.sdk.setName(compiler.options.name);
      }

      setSDK(this.sdk);

      compiler.hooks.afterPlugins.tap(
        pluginTapPostOptions,
        this.afterPlugins.bind(this, compiler),
      );
      compiler.hooks.done.tapPromise(
        {
          ...pluginTapPostOptions,
          stage: pluginTapPostOptions.stage! + 100,
        },
        this.done.bind(this, compiler),
      );

      // TODO: to fix the TypeError: Type instantiation is excessively deep and possibly infinite.
      // @ts-ignore
      new InternalSummaryPlugin<Plugin.BaseCompilerType<'rspack'>>(this).apply(
        compiler,
      );

      if (this.options.features.loader) {
        new BuildUtilLoader.ProbeLoaderPlugin().apply(compiler);
        // add loader page to client
        this.sdk.addClientRoutes([
          Manifest.RsdoctorManifestClientRoutes.Loaders,
        ]);

        if (!Loader.isVue(compiler)) {
          new InternalLoaderPlugin<Plugin.BaseCompilerType<'rspack'>>(
            this,
          ).apply(compiler);
        }
      }

      if (this.options.features.plugins) {
        new InternalPluginsPlugin<Plugin.BaseCompilerType<'rspack'>>(
          this,
        ).apply(compiler);
      }

      if (this.options.features.bundle) {
        new InternalBundlePlugin<Plugin.BaseCompilerType<'rspack'>>(this).apply(
          compiler,
        );
      }

      if (this.options.features.resolver) {
        new InternalResolverPlugin<Plugin.BaseCompilerType<'rspack'>>(
          this,
        ).apply(compiler);
      }

      new InternalRulesPlugin(this).apply(compiler);

      // Keep bundler diagnostics reporting separate from Rsdoctor lint messages.
      new InternalErrorReporterPlugin(this).apply(compiler);

      // apply Rspack native plugin to improve the performance
      const RsdoctorRspackNativePlugin =
        compiler.webpack.experiments?.RsdoctorPlugin;
      if (RsdoctorRspackNativePlugin) {
        logger.debug('[RspackNativePlugin] Enabled');
        const enableNativePlugin = this.options.experiments?.enableNativePlugin;
        new RsdoctorRspackNativePlugin({
          moduleGraphFeatures: enableNativePlugin?.moduleGraph ?? true,
          chunkGraphFeatures: enableNativePlugin?.chunkGraph ?? true,
          sourceMapFeatures: {
            cheap: false,
            module: false,
          },
        }).apply(compiler);
      }
    } finally {
      timeEnd('RsdoctorRspackPlugin.apply');
    }
  }

  /**
   * @description Generate ModuleGraph and ChunkGraph from stats and Rspack module APIs.
   * @param {Compiler} compiler
   * @return {*}
   * @memberof RsdoctorRspackPlugin
   */
  public ensureModulesChunksGraphApplied(
    compiler: Plugin.BaseCompilerType<'rspack'>,
  ) {
    ensureModulesChunksGraphFn(compiler, this);
  }

  public afterPlugins = (compiler: Plugin.BaseCompilerType<'rspack'>): void => {
    time('RsdoctorRspackPlugin.afterPlugins');
    try {
      this.getRspackConfig(compiler);
    } finally {
      timeEnd('RsdoctorRspackPlugin.afterPlugins');
    }
  };

  public done = async (
    compiler: Plugin.BaseCompilerType<'rspack'>,
  ): Promise<void> => {
    time('RsdoctorRspackPlugin.done');
    try {
      logger.debug('[RsdoctorRspackPlugin] bootstrap(start) in done()');
      await this.sdk.bootstrap();
      logger.debug('[RsdoctorRspackPlugin] bootstrap(end) in done()');

      this.sdk.addClientRoutes([
        ManifestType.RsdoctorManifestClientRoutes.Overall,
      ]);

      if (this.outsideInstance && 'parent' in this.sdk) {
        this.sdk.parent.master.setOutputDir(
          path.resolve(
            this.options.output.reportDir || compiler.outputPath,
            this.options.output.mode === SDK.IMode[SDK.IMode.brief]
              ? ''
              : `./${Constants.RsdoctorOutputFolder}`,
          ),
        );
      }

      this.sdk.setOutputDir(
        path.resolve(
          this.options.output.reportDir || compiler.outputPath,
          this.options.output.mode === SDK.IMode[SDK.IMode.brief]
            ? ''
            : `./${Constants.RsdoctorOutputFolder}`,
        ),
      );
      await this.sdk.writeStore();
      if (!this.options.disableClientServer) {
        // If it's brief mode, open the static report page instead of the local server page.
        if (this.options.output.mode === SDK.IMode[SDK.IMode.brief]) {
          // Use extracted common function to handle brief mode
          await handleBriefModeReport(
            this.sdk,
            this.options,
            this.options.disableClientServer,
          );
        } else {
          await this.sdk.server.openClientPage('homepage');
        }
      }

      if (
        this.options.disableClientServer ||
        (this.options.output.mode === SDK.IMode[SDK.IMode.brief] &&
          Array.isArray(this.options.output.options?.type) &&
          this.options.output.options.type.length === 1 &&
          this.options.output.options.type[0] === 'json')
      ) {
        await this.sdk.dispose();
      }
    } finally {
      timeEnd('RsdoctorRspackPlugin.done');
    }
  };

  public getRspackConfig(compiler: Plugin.BaseCompilerType<'rspack'>) {
    time('RsdoctorRspackPlugin.getRspackConfig');
    try {
      if (compiler.isChild()) return;

      // Use extracted common function to process configuration
      const configuration = processCompilerConfig(compiler.options);

      const rspackVersion =
        compiler.webpack?.rspackVersion || compiler.webpack?.version;

      // Save Rspack configuration to sdk.
      this.sdk.reportConfiguration({
        name: 'rspack',
        version: rspackVersion || 'unknown',
        config: configuration,
        root: findRoot() || '',
      });
    } finally {
      timeEnd('RsdoctorRspackPlugin.getRspackConfig');
    }
  }
}

```

### packages/sdk/src/sdk/multiple/primary.ts
```
import path from 'path';
import { Manifest, SDK } from '@rsdoctor/types';
import { RsdoctorSDK } from '../sdk';
import { RsdoctorSlaveServer } from './server';
import type { RsdoctorSDKController } from './controller';

let id = 1;

interface RsdoctorSlaveSDKOptions {
  name: string;
  /**
   * use to sort for display in the client page.
   * the smaller the front.
   * @default 1
   */
  stage?: number;
  extraConfig?: SDK.SDKOptionsType;
  controller: RsdoctorSDKController;
  type: SDK.ToDataType;
}

export class RsdoctorPrimarySDK
  extends RsdoctorSDK
  implements SDK.RsdoctorBuilderSDKInstance
{
  id: number;

  parent: RsdoctorSDKController;

  public readonly stage: number;

  public dependencies: Array<string> | undefined;

  private uploadPieces!: Promise<void>;

  private finishUploadPieceSwitch!: () => void;

  constructor({
    name,
    stage,
    controller,
    extraConfig,
    type,
  }: RsdoctorSlaveSDKOptions) {
    super({ name, root: controller.root });

    const lastSdk = controller.getLastSdk();
    const port = lastSdk ? lastSdk.server.port + 1 : this.server.port;

    this.id = id++;
    this.stage = typeof stage === 'number' ? stage : 1;
    this.extraConfig = extraConfig;
    this.parent = controller;
    this.server = new RsdoctorSlaveServer(this, port);
    this.type = type;
    this.setName(name);
    this.clearSwitch();
  }

  private clearSwitch() {
    this.uploadPieces = new Promise<void>((resolve) => {
      this.finishUploadPieceSwitch = resolve;
    });
  }

  get isMaster() {
    return this.parent.master === this;
  }

  protected async writePieces(): Promise<void> {
    const { name, parent, isMaster, outputDir, finishUploadPieceSwitch } = this;
    this.setOutputDir(
      isMaster
        ? outputDir
        : path.join(
            parent.master.outputDir,
            '.slaves',
            name.replace(/\s+/g, '-'),
          ),
    );
    await super.writePieces(this.getStoreData());
    finishUploadPieceSwitch?.();
  }

  protected async writeManifest() {
    const { parent, cloudData, dependencies } = this;

    if (!dependencies?.length) {
      await Promise.all(
        this.parent.slaves
          .filter((item) => !item.dependencies?.length)
          .map((item) => item.uploadPieces),
      );
    }

    if (cloudData) {
      cloudData.name = this.name;
      cloudData.series = parent.getSeriesData();
    }

    const result = await super.writeManifest();
    this.clearSwitch();
    return result;
  }

  getSeriesData(serverUrl = false): Manifest.RsdoctorManifestSeriesData[] {
    return this.parent.getSeriesData(serverUrl);
  }

  setName(name: string) {
    this._name = this.parent.hasName(name) ? `${name}-${id}` : name;
  }

  getManifestData(): Manifest.RsdoctorManifestWithShardingFiles {
    const data = super.getManifestData();
    data.name = this.name;
    data.series = this.getSeriesData(true);
    return data;
  }
}

```

### packages/sdk/src/sdk/multiple/server.ts
```
import { Server } from '@rsdoctor/utils/build';
import { RsdoctorServer } from '../server';
import type { RsdoctorPrimarySDK } from './primary';

export class RsdoctorSlaveServer extends RsdoctorServer {
  protected sdk: RsdoctorPrimarySDK;

  constructor(sdk: RsdoctorPrimarySDK, port = Server.defaultPort) {
    super(sdk, port);
    this.sdk = sdk;
  }

  async openClientPage(...args: unknown[]) {
    if (this.sdk.isMaster) {
      return super.openClientPage(...(args as ['homepage']));
    }

    return Promise.resolve();
  }
}

```

### packages/sdk/src/sdk/sdk/index.ts
```
import fs from 'node:fs';
import fse from 'fs-extra';
import path from 'path';
import { createRequire } from 'module';
import { DevToolError } from '@rsdoctor/utils/error';
import { Common, Constants, Manifest, SDK } from '@rsdoctor/types';
import { RawSourceMap, SourceMapConsumer } from 'source-map';
import { ModuleGraph, ChunkGraph, PackageGraph } from '@rsdoctor/graph';
import { logger } from '@rsdoctor/utils/logger';
import { RsdoctorServer } from '../server';
import { RsdoctorFakeServer } from '../server/fakeServer';
import { RsdoctorRspackSDKOptions } from './types';
import { SDKCore } from './core';
import { Algorithm } from '@rsdoctor/utils/common';
import { Lodash } from '@rsdoctor/utils/common';
import { findRoot } from '../utils';
import { decycle } from '@rsdoctor/utils/common';

export * from '../utils/openBrowser';
export * from '../utils/base';

const require = createRequire(import.meta.url);
export class RsdoctorSDK<
  T extends RsdoctorRspackSDKOptions = RsdoctorRspackSDKOptions,
>
  extends SDKCore<T>
  implements SDK.RsdoctorBuilderSDKInstance
{
  public server: RsdoctorServer;

  public extraConfig: SDK.SDKOptionsType | undefined;

  public type: SDK.ToDataType;

  public root: string;

  private _summary: SDK.SummaryData = { costs: [] };

  private _configs: SDK.ConfigData = [];

  private _errors: DevToolError[] = [];

  private _loader: SDK.LoaderData = [];

  private _loaderStart: SDK.LoaderData = [];

  private _resolver: SDK.ResolverData = [];

  private _plugin: SDK.PluginData = {};

  private _moduleGraph: SDK.ModuleGraphInstance = new ModuleGraph();

  private _chunkGraph: SDK.ChunkGraphInstance = new ChunkGraph();

  private _rawSourceMapCache = new Map<string, RawSourceMap>();

  private _sourceMap = new Map<string, SourceMapConsumer>();

  private _packageGraph!: SDK.PackageGraphInstance;

  constructor(options: T) {
    super(options);
    this.server = options.config?.noServer
      ? new RsdoctorFakeServer(this, undefined)
      : new RsdoctorServer(this, options.port, {
          innerClientPath: options.config?.innerClientPath || '',
          printServerUrl: options.config?.printLog?.serverUrls,
        });
    this.type = Lodash.isNumber(options.type)
      ? options.type
      : SDK.ToDataType.Normal;
    this.extraConfig = options.config;
    this.root = findRoot() ?? '';
  }

  async bootstrap() {
    logger.debug(`${Date.now()}`, '[RsdoctorSDK][bootstrap start]');
    if (this.server) {
      await this.server.bootstrap();
    }
    await super.bootstrap();
    logger.debug(
      `${Date.now()} ${this.server.origin}`,
      '[RsdoctorSDK][bootstrap end]',
    );
  }

  async dispose() {
    logger.debug(`${Date.now()}`, '[RsdoctorSDK][dispose start]');
    if (this.server) {
      await this.server.dispose();
    }
    await super.dispose();
    logger.debug(`${Date.now()}`, '[RsdoctorSDK][dispose end]');
  }

  async applyErrorFix(id: number) {
    const { _errors: errors } = this;
    const error = errors.find((err) => err.id === id);

    if (!error || !error.path || !error.fixData || error.fixData.isFixed) {
      return;
    }

    const { path: filePath, fixData } = error;
    const sameFileErrors = errors.filter(
      (item) => item.path === filePath && item !== error,
    );
    let content = (await fs.promises.readFile(filePath, 'utf-8')).toString();

    // Application of current modification.
    const startTxt = content.substring(0, fixData.start);
    const endTxt = content.substring(fixData.end, content.length);
    const offset =
      (fixData.newText ?? '').length - (fixData.end - fixData.start);

    // Modified text.
    content = startTxt + fixData.newText + endTxt;

    // The remaining modifications of the same document need to be recalculated.
    for (const other of sameFileErrors) {
      const { fixData: otherFixData } = other;

      if (!otherFixData) {
        continue;
      }

      // After the modified text, the offset needs to be corrected.
      if (otherFixData.start >= fixData.end) {
        otherFixData.start += offset;
        otherFixData.end += offset;
      }
    }

    // Modify the write to the hard disk.
    await fs.promises.writeFile(filePath, content);
  }

  clear() {
    this._errors = [];
    this._loader = [];
    this._resolver = [];
    this._plugin = {};
    this._moduleGraph = new ModuleGraph();
    this._chunkGraph = new ChunkGraph();
  }

  clearSourceMapCache(): void {
    this._rawSourceMapCache = new Map();
    this._sourceMap = new Map();
  }

  async getSourceMap(file: string): Promise<SourceMapConsumer | undefined> {
    const { _sourceMap: sourceMap, _rawSourceMapCache: rawMap } = this;

    if (sourceMap.has(file)) {
      return sourceMap.get(file)!;
    }

    const rawData = rawMap.get(file);

    // There is no data, or illegal data.
    if (
      !rawData ||
      rawData.version < 0 ||
      !rawData.sourcesContent?.[0] ||
      !rawData.mappings
    ) {
      return Promise.resolve(undefined);
    }

    try {
      const result = await new SourceMapConsumer(rawData);
      sourceMap.set(file, result);
      return result;
    } catch {
      // TODO: Specific errors need to be checked.
      return Promise.resolve(undefined);
    }
  }

  reportSourceMap(data: RawSourceMap): void {
    this._rawSourceMapCache.set(data.file, data);
  }

  reportConfiguration(config: SDK.ConfigData[0]) {
    config.root ??= this.root;
    this._configs.push(config);
    this.onDataReport();
  }

  reportError(errors: Error[]) {
    errors.forEach((item) => {
      this._errors.push(
        DevToolError.from(item, {
          code: this.name,
        }),
      );
    });
    this.onDataReport();
  }

  reportLoader(data: SDK.LoaderData) {
    data.forEach((item) => {
      if (this.extraConfig?.mode === SDK.IMode[SDK.IMode.brief]) {
        item.loaders.forEach((_loader) => {
          _loader.input = undefined;
          _loader.result = undefined;
        });
      }

      // find by resource.path
      let match = this._loader.find(
        (e) => e.resource.path === item.resource.path,
      );
      if (match) {
        match.loaders.push(...item.loaders);
      } else {
        match = item;
        this._loader.push(item);
      }

      match.loaders.sort((a, b) => {
        // default sort by call timestamp
        if (a.startAt !== b.startAt) {
          return a.startAt - b.startAt;
        }

        if (a.isPitch) {
          if (b.isPitch) {
            return a.loaderIndex - b.loaderIndex;
          }
          // [a, b]
          return -1;
        }

        if (b.isPitch) {
          // [b, a]
          return 1;
        }

        return b.loaderIndex - a.loaderIndex;
      });
    });
    this.onDataReport();
  }

  reportLoaderStartOrEnd(data: SDK.ResourceLoaderData) {
    // Just one loader data in array list.
    const _builtinLoader = data.loaders[0];
    if (_builtinLoader.startAt) {
      this._loaderStart.push(data);
    } else if (_builtinLoader.endAt) {
      const matchLoaderStart = this._loaderStart.find(
        (e) =>
          e.resource.path === data.resource.path &&
          e.loaders[0].loader === _builtinLoader.loader,
      );

      if (matchLoaderStart) {
        matchLoaderStart.loaders[0].result = _builtinLoader.result;
        matchLoaderStart.loaders[0].endAt = _builtinLoader.endAt;
        this.reportLoader([matchLoaderStart]);
      }
    }
  }

  reportResolver(data: SDK.ResolverData): void {
    data.forEach((item) => this._resolver.push(item));
    this.onDataReport();
  }

  reportPlugin(data: SDK.PluginData): void {
    Object.keys(data).forEach((hook) => {
      if (!this._plugin[hook]) {
        this._plugin[hook] = data[hook];
      } else {
        data[hook].forEach((item) => {
          this._plugin[hook].push(item || undefined);
        });
      }
    });
    this.onDataReport();
  }

  reportModuleGraph(data: SDK.ModuleGraphInstance): void {
    logger.debug(`data size: ${data.size()}`, '[SDK.reportModuleGraph][start]');
    this._moduleGraph.fromInstance(data as ModuleGraph);
    this.createPackageGraph();
    this.onDataReport();
    logger.debug(
      `sdk._moduleGraph size: ${this._moduleGraph.size()}`,
      '[SDK reportModuleGraph][end]',
    );
  }

  reportPackageGraph(data: SDK.PackageGraphInstance): void {
    logger.debug('[SDK.reportPackageGraph][start]');
    if (!this._packageGraph) {
      this._packageGraph = data;
    }
    this.onDataReport();
    logger.debug(
      `sdk._packageGraph size: ${this._packageGraph.getPackages().length}`,
      '[SDK reportPackageGraph][end]',
    );
  }

  reportChunkGraph(data: SDK.ChunkGraphInstance): void {
    this._chunkGraph.addAsset(...data.getAssets());
    this._chunkGraph.addChunk(...data.getChunks());
    this._chunkGraph.addEntryPoint(...data.getEntryPoints());
    this.onDataReport();
  }

  reportSummaryData(part: Partial<SDK.SummaryData>): void {
    const keys = ['costs'] as Array<keyof SDK.SummaryData>;

    for (const key of keys) {
      const v = part[key];
      if (!v) continue;
      if (typeof v === 'object') {
        if (Array.isArray(v)) {
          (this._summary[key] as unknown[]) = [
            ...((this._summary[key] as Array<any>) || []),
            ...v,
          ];
        } else {
          (this._summary[key] as Common.PlainObject) = {
            ...((this._summary[key] as Common.PlainObject) || {}),
            ...(v as Common.PlainObject),
          };
        }
      } else {
        (this._summary[key] as unknown) = v;
      }
    }

    this.onDataReport();
  }

  createPackageGraph() {
    logger.debug(
      `sdk._moduleGraph size: ${this._moduleGraph.size()}`,
      '[SDK.createPackageGraph][start]',
    );
    if (!this._packageGraph) {
      const pkgGraph = PackageGraph.fromModuleGraph(
        this._moduleGraph,
        this.root,
        (path: string) => {
          try {
            const exists = fs.existsSync(path);
            if (exists) {
              // TODO: it's too much logs, this needs to be optimized
              // logger.debug(
              //   `sdk.PackageGraph package.json exists: ${exists}, path: ${path}`,
              //   '[SDK.createPackageGraph][load]',
              // );
              const res = fse.readJsonSync(path);
              return res;
            }
          } catch (error) {
            const { message, stack } = error as Error;
            logger.debug(
              () =>
                `sdk.createPackageGraph error, path: ${path}, error message: ${
                  stack || message
                }`,
              '[SDK.createPackageGraph][error]',
            );
          }
        },
      );
      this._packageGraph = pkgGraph;
      logger.debug(
        `sdk._packageGraph packages: ${
          this._packageGraph.getPackages().length
        }`,
        '[SDK.createPackageGraph][end]',
      );
    }
  }

  public async writeStore(options?: SDK.WriteStoreOptionsType) {
    logger.debug(`sdk.writeStore has run.`, '[SDK.writeStore][end]');
    let htmlPath = '';
    if (this.extraConfig?.mode === SDK.IMode[SDK.IMode.brief]) {
      const clientHtmlPath = this.extraConfig.innerClientPath
        ? this.extraConfig.innerClientPath
        : require.resolve('@rsdoctor/client');

      if (this.extraConfig?.brief?.type?.includes('json')) {
        const data = this.getStoreData();
        const clientRoutes = this.getClientRoutes();
        const jsonData = {
          data,
          clientRoutes,
        };

        fs.mkdirSync(this.outputDir, { recursive: true });
        fs.writeFileSync(
          path.resolve(
            this.outputDir,
            this.extraConfig.brief.jsonOptions?.fileName ??
              'rsdoctor-data.json',
          ),
          JSON.stringify(jsonData),
        );
      }
      if (this.extraConfig.brief?.type?.includes('html')) {
        htmlPath = this.inlineScriptsAndStyles(clientHtmlPath);
      }
      return htmlPath;
    }
    return this.saveManifest(this.getStoreData(), options || {});
  }

  public getStoreData(): SDK.BuilderStoreData {
    // rslint-disable-next-line @typescript-eslint/no-this-alias
    const ctx = this;
    const briefOptions = this.extraConfig?.brief;
    const sections = briefOptions?.jsonOptions?.sections;
    const isJsonType = briefOptions?.type?.includes('json');

    return {
      get hash() {
        return ctx.hash;
      },
      get root() {
        return ctx.root;
      },
      get envinfo() {
        return ctx._envinfo;
      },
      get pid() {
        return ctx.pid;
      },
      get errors() {
        // In brief mode with sections control, check if rules section is enabled
        if (isJsonType && sections && !sections.rules) {
          return [];
        }
        return ctx._errors.map((err) => err.toData());
      },
      get configs() {
        return ctx._configs.slice();
      },
      get summary() {
        return { ...ctx._summary };
      },
      get resolver() {
        return ctx._resolver.slice();
      },
      get loader() {
        return ctx._loader.slice();
      },
      get moduleGraph() {
        // In brief mode with sections control, check if moduleGraph section is enabled
        if (isJsonType && sections && !sections.moduleGraph) {
          return {
            dependencies: [],
            modules: [],
            moduleGraphModules: [],
            exports: [],
            sideEffects: [],
            variables: [],
            layers: [],
          };
        }
        return ctx._moduleGraph.toData({
          contextPath: ctx._configs?.[0]?.config?.context || '',
          briefOptions,
        });
      },
      get chunkGraph() {
        // In brief mode with sections control, check if chunkGraph section is enabled
        if (isJsonType && sections && !sections.chunkGraph) {
          return {
            assets: [],
            chunks: [],
            entrypoints: [],
          };
        }
        return ctx._chunkGraph.toData(ctx.type);
      },
      get moduleCodeMap() {
        if (ctx.extraConfig?.mode === SDK.IMode[SDK.IMode.brief]) {
          return {};
        }
        return ctx._moduleGraph.toCodeData(ctx.type);
      },
      get plugin() {
        return { ...ctx._plugin };
      },
      get packageGraph() {
        return ctx._packageGraph
          ? ctx._packageGraph.toData()
          : {
              packages: [],
              dependencies: [],
            };
      },
      get treeShaking() {
        if (ctx.extraConfig?.mode === SDK.IMode[SDK.IMode.brief]) {
          return undefined;
        }
        if (!ctx.extraConfig?.features?.treeShaking) {
          return undefined;
        }
        return ctx._moduleGraph.toTreeShakingData();
      },
      get otherReports() {
        return { treemapReportHtml: '' };
      },
    };
  }

  public getManifestData(): Manifest.RsdoctorManifestWithShardingFiles {
    const dataValue = this.getStoreData();
    const data: Manifest.RsdoctorManifestWithShardingFiles = {
      client: {
        enableRoutes: this.getClientRoutes(),
      },
      data: Object.keys(dataValue).reduce((t, e) => {
        const _e = e as keyof SDK.BuilderStoreData;
        if (dataValue[_e] && typeof dataValue[_e] === 'object') {
          t[e] = [
            `${this.server.origin}${SDK.ServerAPI.API.LoadDataByKey}/${e}`,
          ];
        } else {
          t[e] = dataValue[_e];
        }

        return t;
      }, {} as Common.PlainObject) as unknown as Manifest.RsdoctorManifestWithShardingFiles['data'],
      __LOCAL__SERVER__: true,
      __SOCKET__PORT__: this.server.socketUrl.port.toString(),
      __SOCKET__URL__: this.server.socketUrl.socketUrl,
    };

    return data;
  }

  public getRuleContext(
    _options: SDK.RuntimeContextOptions,
  ): SDK.RuntimeContext {
    this.createPackageGraph();

    return {
      root: this.root,
      errors: this._errors.slice(),
      configs: this._configs.slice(),
      moduleGraph: this._moduleGraph,
      chunkGraph: this._chunkGraph,
      packageGraph: this._packageGraph,
      loader: this._loader.slice(),
      otherReports: { treemapReportHtml: '' },
    };
  }

  public onDataReport(): void | Promise<void> {
    this.server.broadcast();
  }

  public addRsdoctorDataToHTML(
    storeData: SDK.BuilderStoreData,
    htmlContent: string,
  ) {
    let compressTextScripts = `<script>window.${Constants.WINDOW_RSDOCTOR_TAG}={}</script>`;
    for (const key of Object.keys(storeData)) {
      const data = storeData[key];

      const jsonStrFn = () => {
        try {
          if (key === 'configs') {
            return JSON.stringify(decycle(data));
          }
          return JSON.stringify(data);
        } catch (error) {
          console.error(error);
          return '';
        }
      };
      const compressText = Algorithm.compressText(jsonStrFn());

      compressTextScripts = `${compressTextScripts} <script>window.${Constants.WINDOW_RSDOCTOR_TAG}.${key}=${JSON.stringify(compressText)}</script>`;
    }
    compressTextScripts = `${compressTextScripts} <script>window.${Constants.WINDOW_RSDOCTOR_TAG}.enableRoutes=${JSON.stringify(this.getClientRoutes())}</script>`;

    htmlContent = htmlContent.replace('<body>', `<body>${compressTextScripts}`);

    return htmlContent;
  }

  public inlineScriptsAndStyles(htmlFilePath: string) {
    // Helper function to inline JavaScript files
    function inlineScripts(basePath: string, scripts: string[]): string {
      return scripts
        .map((src) => {
          const scriptPath = resolveFilePath(basePath, src);
          try {
            const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
            return `<script>${scriptContent}</script>`;
          } catch (error) {
            console.error(`Could not read script at ${scriptPath}:`, error);
            return '';
          }
        })
        .join('');
    }

    function resolveFilePath(basePath: string, filePath: string): string {
      if (filePath.startsWith('/')) {
        return path.resolve(basePath, filePath.slice(1));
      }

      return path.resolve(basePath, filePath);
    }

    // Helper function to inline CSS files
    function inlineCss(basePath: string, cssFiles: string[]): string {
      return cssFiles
        .map((href) => {
          const cssPath = resolveFilePath(basePath, href);
          try {
            const cssContent = fs.readFileSync(cssPath, 'utf-8');
            return `<style>${cssContent}</style>`;
          } catch (error) {
            console.error(`Could not read CSS at ${cssPath}:`, error);
            return '';
          }
        })
        .join('');
    }

    // Path to your HTML file
    let htmlContent = fs.readFileSync(htmlFilePath, 'utf-8');

    // Base path to the resources
    const basePath = path.dirname(htmlFilePath);

    // Extract scripts and links from the HTML
    const scriptSrcs = Array.from(
      htmlContent.matchAll(
        /<script\s+(?:defer="defer"|defer)\s+src=["'](.+?)["']><\/script>/g,
      ),
      (m) => m[1],
    );
    const cssHrefs = Array.from(
      htmlContent.matchAll(/<link\s+href=["'](.+?)["']\s+rel="stylesheet">/g),
      (m) => m[1],
    );

    // Remove all <script> tags
    htmlContent = htmlContent.replace(
      /<script\s+.*?src=["'].*?["']><\/script>/g,
      '',
    );

    // Remove all <link rel="stylesheet"> tags
    htmlContent = htmlContent.replace(
      /<link\s+.*?rel=["']stylesheet["'].*?>/g,
      '',
    );

    // Inline scripts and CSS
    const inlinedScripts = inlineScripts(basePath, scriptSrcs);
    const inlinedCss = inlineCss(basePath, cssHrefs);

    const index = htmlContent.indexOf('</body>');
    htmlContent =
      htmlContent.slice(0, index) +
      inlinedCss +
      inlinedScripts +
      htmlContent.slice(index);
    htmlContent = this.addRsdoctorDataToHTML(this.getStoreData(), htmlContent);

    // Output the processed HTML content
    const outputFilePath = path.resolve(
      this.outputDir,
      this.extraConfig?.brief?.htmlOptions?.reportHtmlName ||
        'rsdoctor-report.html',
    );

    fs.mkdirSync(path.dirname(outputFilePath), { recursive: true });

    fs.writeFileSync(outputFilePath, htmlContent, {
      encoding: 'utf-8',
      flag: 'w',
    });
    return outputFilePath;
  }
}

```

### packages/sdk/src/sdk/server/fakeServer.ts
```
import { SDK } from '@rsdoctor/types';
import { Server } from '@rsdoctor/utils/build';
import { RsdoctorServer } from '.';

export class RsdoctorFakeServer extends RsdoctorServer {
  constructor(
    protected sdk: SDK.RsdoctorBuilderSDKInstance,
    port = Server.defaultPort,
  ) {
    super(sdk, port);
    this.sdk = sdk;
  }

  async openClientPage() {}
}

```

### packages/sdk/src/sdk/server/index.ts
```
import { Common, SDK, Thirdparty, Client } from '@rsdoctor/types';
import { Server } from '@rsdoctor/utils/build';
import serve from 'sirv';
import { Bundle, GlobalConfig } from '@rsdoctor/utils/common';
import assert from 'assert';
import bodyParser from 'body-parser';
import cors from 'cors';
import { PassThrough } from 'stream';
import { Socket } from './socket';
import { Router } from './router';
import * as APIs from './apis';
import { chalk, logger } from '@rsdoctor/utils/logger';
import { openBrowser } from '@/sdk/utils/openBrowser';
import path from 'path';
import { getLocalIpAddress } from './utils';
import { Lodash } from '@rsdoctor/utils/common';
import { createRequire } from 'module';
import { ServerResponse } from 'http';

const require = createRequire(import.meta.url);
export * from './utils';

/** Path for launch-editor: open file in editor from the UI (see https://github.com/yyx990803/launch-editor) */
const OPEN_IN_EDITOR_PATH = '/__open-in-editor';

export type ISocketType = { port: number; socketUrl: string };

export class RsdoctorServer implements SDK.RsdoctorServerInstance {
  private _server!: Common.PromiseReturnType<typeof Server.createServer>;

  public port: number;

  private _socket?: Socket;

  private disposed = true;

  private _router: Router;

  private _innerClientPath: string;

  private _printServerUrl: boolean;

  constructor(
    protected sdk: SDK.RsdoctorBuilderSDKInstance,
    port = Server.defaultPort,
    config?: { innerClientPath?: string; printServerUrl?: boolean },
  ) {
    assert(typeof port === 'number');
    // maybe the port will be rewrite in bootstrap()
    this.port = port;
    this._router = new Router({ sdk, server: this, apis: Object.values(APIs) });
    this._innerClientPath = config?.innerClientPath || '';
    this._printServerUrl = Lodash.isUndefined(config?.printServerUrl)
      ? true
      : config?.printServerUrl;
  }

  public get app(): SDK.RsdoctorServerInstance['app'] {
    return this._server.app;
  }

  public get host(): string {
    const host = getLocalIpAddress();
    return host;
  }

  public get origin(): string {
    return `http://${this.host}:${this.port}`;
  }

  public get socketUrl(): ISocketType {
    return {
      port: this.port,
      socketUrl: `ws://localhost:${this.port}`,
    };
  }

  public get innerClientPath(): string {
    return this._innerClientPath;
  }

  async bootstrap() {
    if (!this.disposed) {
      return;
    }

    const port = Server.getPortSync(this.port);
    // rewrite port when the default port is unavailable
    this.port = port;
    this._server = await Server.createServer(port);
    this._socket = new Socket({
      sdk: this.sdk,
      server: this._server.server,
      port: this.port,
    });
    await this._socket.bootstrap();

    GlobalConfig.writeMcpPort(this.port, this.sdk.name);

    logger.debug(
      `Successfully wrote mcp.json for ${chalk.cyan(this.sdk.name)} builder`,
    );

    this.disposed = false;

    this.app.use(cors());
    this.app.use(bodyParser.json({ limit: '500mb' }));
    const clientHtmlPath = this._innerClientPath
      ? this._innerClientPath
      : require.resolve('@rsdoctor/client');
    const clientDistPath = path.resolve(clientHtmlPath, '..');
    this.app.use(
      serve(clientDistPath, {
        dev: true,
      }),
    );

    // launch-editor: open file in editor (VSCode, Cursor, etc.) from the UI
    this.app.use(
      OPEN_IN_EDITOR_PATH,
      (
        req: Thirdparty.connect.IncomingMessage,
        res: ServerResponse,
        next: () => void,
      ) => {
        if (req.method !== 'GET' && req.method !== 'HEAD') {
          return next();
        }
        const url = new URL(req.url || '', `http://localhost`);
        const file = url.searchParams.get('file');
        const editor = url.searchParams.get('editor') || undefined;
        if (!file) {
          res.statusCode = 400;
          res.end('Missing file parameter');
          return;
        }
        try {
          const launch = require('launch-editor') as (
            file: string,
            specifiedEditor?: string,
            onErrorCallback?: (
              fileName: string,
              errorMessage: string | null,
            ) => void,
          ) => void;
          let responded = false;
          const safeEnd = (code: number, body: string) => {
            if (responded) return;
            responded = true;
            res.statusCode = code;
            res.end(body);
          };
          launch(file, editor, (_fileName, errorMessage) => {
            if (errorMessage) {
              safeEnd(500, errorMessage);
            }
          });

          setTimeout(() => {
            safeEnd(200, '');
          }, 200);
        } catch (err) {
          if (!res.writableEnded) {
            res.statusCode = 500;
            res.end((err as Error).message);
          }
        }
      },
    );

    await this._router.setup();

    process.once('exit', () => this.dispose());
    process.once('SIGINT', () => this.dispose(0));
    process.once('SIGTERM', () => this.dispose(0));

    process.once('unhandledRejection', (reason: unknown) => {
      console.error('Unhandled promise rejection:', reason);
      this.dispose(1);
    });

    process.once('uncaughtException', (err: Error, origin: string) => {
      console.error('Uncaught exception:', err);
      if (origin) {
        console.error('Exception origin:', origin);
      }
      this.dispose(1);
    });
  }

  protected wrapNextHandleFunction(
    method: 'GET' | 'POST',
    cb: (
      ...args: Parameters<Thirdparty.connect.NextHandleFunction>
    ) => Common.PlainObject | string,
  ): Thirdparty.connect.NextHandleFunction {
    return async (req, res, next) => {
      const m = req.method?.toUpperCase();
      if (m === method) {
        try {
          const body = await cb(req, res, next);

          res.setHeader('Access-Control-Allow-Origin', '*');
          res.setHeader('Access-Control-Allow-Credentials', 'true');
          res.statusCode = 200;

          if (Buffer.isBuffer(body)) {
            res.setHeader('Content-Length', body.byteLength);
            const ps = new PassThrough();
            ps.write(body);
            ps.end();
            ps.pipe(res);
          } else if (body && typeof body === 'object') {
            res.writeHead(200, {
              'Content-Type': 'application/json;utf-8',
            });
            res.write(JSON.stringify(body));
            res.end();
          } else {
            res.writeHead(200).end(body);
          }
        } catch (error) {
          res.statusCode = 500;
          res.end((error as Error).message);
          return next(error);
        }
        return;
      }
      await next();
    };
  }

  public proxy(
    api: SDK.ServerAPI.API,
    method: 'GET' | 'POST',
    cb: (
      ...args: Parameters<Thirdparty.connect.NextHandleFunction>
    ) => Common.PlainObject | string,
  ) {
    let idx = this.app.stack.findIndex((e) => e.route === api);
    if (idx === -1) {
      idx = this.app.stack.length - 1;
    }
    this.app.stack.splice(idx, 0, {
      route: api,
      handle: this.wrapNextHandleFunction(method, cb),
    });
  }

  public get: SDK.RsdoctorServerInstance['get'] = (route, cb) => {
    const { app } = this;
    app.use(route, this.wrapNextHandleFunction('GET', cb));
    return app;
  };

  public post: SDK.RsdoctorServerInstance['post'] = (route, cb) => {
    const { app } = this;
    app.use(route, this.wrapNextHandleFunction('POST', cb));
    return app;
  };

  public getClientUrl(
    route: Client.RsdoctorClientRoutes,
    baselineUrl: string,
    currentUrl: string,
  ): string;

  public getClientUrl(route?: 'homepage'): string;

  public getClientUrl(route = 'homepage', ...args: unknown[]) {
    const relativeUrl = SDK.ServerAPI.API.EntryHtml;

    switch (route) {
      case Client.RsdoctorClientRoutes.BundleDiff: {
        const [baseline, current] = args as string[];
        const qs = Bundle.getBundleDiffPageQueryString([baseline, current]);
        return `${relativeUrl}${qs}#${Client.RsdoctorClientRoutes.BundleDiff}`;
      }
      default:
        return relativeUrl;
    }
  }

  public async openClientPage(
    route: Client.RsdoctorClientRoutes,
    baselineUrl: string,
    currentUrl: string,
  ): Promise<void>;

  public async openClientPage(route?: 'homepage'): Promise<void>;

  public async openClientPage(...args: unknown[]) {
    const relativeUrl = this.getClientUrl(
      ...(args as Parameters<SDK.RsdoctorServerInstance['getClientUrl']>),
    );

    const needEncodeURI = args[0] === Client.RsdoctorClientRoutes.BundleDiff;
    const url = `http://${this.host}:${this.port}${relativeUrl}`;
    const localhostUrl = `http://localhost:${this.port}${relativeUrl}`;
    await openBrowser(localhostUrl, !needEncodeURI);
    if (this._printServerUrl) {
      logger.info(
        `${chalk.green(`${this.sdk.name} compiler's`)} analyzer running on: ${chalk.cyan(url)}`,
      );
    }
  }

  public sendAPIDataToClient<
    T extends SDK.ServerAPI.API | SDK.ServerAPI.APIExtends,
  >(api: T, msg: SDK.ServerAPI.SocketResponseType<T>) {
    this._socket?.sendAPIData(api, msg);
  }

  public async broadcast() {
    await this._socket?.broadcast();
  }

  dispose = async (exitCode?: number) => {
    if (this.disposed) {
      if (exitCode !== undefined) {
        process.exit(exitCode);
      }
      return;
    }
    this.disposed = true;

    if (this._socket) {
      this._socket.dispose();
    }

    if (this._server) {
      await this._server.close();
    }

    if (exitCode !== undefined) {
      process.exit(exitCode);
    }
  };
}

```

### packages/sdk/src/sdk/server/security.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/sdk/src/sdk/server/socket/index.ts
```
import { Common, SDK } from '@rsdoctor/types';
import type { Server } from 'http';
import WebSocket, { WebSocketServer } from 'ws';
import { SocketAPILoader } from './api';

interface SocketOptions {
  sdk: SDK.RsdoctorBuilderSDKInstance;
  server: Server;
  port: number;
}

type Subscription = {
  api: SDK.ServerAPI.API;
  body: Common.PlainObject | null;
};

type SubscriptionRecord = Subscription & {
  count: number;
};

type ClientMessage = {
  type?: string;
  id?: string;
  api?: SDK.ServerAPI.API;
  body?: Common.PlainObject | null;
};

export class Socket {
  protected server?: WebSocketServer;

  protected clients = new Set<WebSocket>();

  protected loader: SocketAPILoader;

  protected map: Map<string, SubscriptionRecord> = new Map();

  protected clientSubscriptions: Map<WebSocket, Set<string>> = new Map();

  constructor(protected options: SocketOptions) {
    this.loader = new SocketAPILoader({ sdk: options.sdk });
  }

  public bootstrap() {
    this.server = new WebSocketServer({ server: this.options.server });
    this.server.on('connection', (client) => {
      this.attachClient(client);
    });
  }

  public attachClient(client: WebSocket) {
    this.clients.add(client);

    if (typeof client.on === 'function') {
      client.on('message', (message) => {
        this.handleClientMessage(message.toString(), client);
      });
      client.on('close', () => {
        this.clients.delete(client);
        this.removeClientSubscriptions(client);
      });
    }
  }

  public async handleClientMessage(raw: string, client?: WebSocket) {
    let message: ClientMessage;
    try {
      message = JSON.parse(raw) as ClientMessage;
    } catch {
      return;
    }

    if (
      !message.api ||
      !Object.values(SDK.ServerAPI.API).includes(message.api)
    ) {
      return;
    }

    if (message.type === 'request') {
      await this.handleAPIRequestMessage(message, client);
      return;
    }

    if (message.type === 'subscribe') {
      this.saveRequestToMap(message.api, message.body ?? null, client);
      return;
    }

    if (message.type === 'unsubscribe') {
      this.removeRequestFromMap(message.api, message.body ?? null, client);
    }
  }

  protected async handleAPIRequestMessage(
    message: ClientMessage,
    client?: WebSocket,
  ) {
    if (!message.id || !client || client.readyState !== WebSocket.OPEN) {
      return;
    }

    try {
      const response = await this.getAPIResponse(message.api!, message.body!);
      client.send(
        JSON.stringify({
          type: 'response',
          id: message.id,
          payload: response.res,
        }),
      );
    } catch (err) {
      client.send(
        JSON.stringify({
          type: 'response',
          id: message.id,
          error: err instanceof Error ? err.message : String(err),
        }),
      );
    }
  }

  public getSubscriptions(): Subscription[] {
    return [...this.map.values()].map(({ api, body }) => ({ api, body }));
  }

  protected saveRequestToMap<T extends SDK.ServerAPI.API>(
    api: T,
    body: SDK.ServerAPI.InferRequestBodyType<T, null> | null = null,
    client?: WebSocket,
  ) {
    const key = this.getSubscriptionKey(api, body);
    if (client) {
      if (!this.clientSubscriptions.has(client)) {
        this.clientSubscriptions.set(client, new Set());
      }
      const subscriptions = this.clientSubscriptions.get(client)!;
      if (subscriptions.has(key)) {
        return;
      }
      subscriptions.add(key);
    }

    const record = this.map.get(key);
    if (record) {
      record.count += 1;
      return;
    }

    this.map.set(key, {
      api,
      body,
      count: 1,
    });
  }

  protected removeRequestFromMap<T extends SDK.ServerAPI.API>(
    api: T,
    body: SDK.ServerAPI.InferRequestBodyType<T, null> | null = null,
    client?: WebSocket,
  ) {
    const key = this.getSubscriptionKey(api, body);
    if (client) {
      const subscriptions = this.clientSubscriptions.get(client);
      if (!subscriptions?.has(key)) {
        return;
      }
      subscriptions.delete(key);
      if (subscriptions.size === 0) {
        this.clientSubscriptions.delete(client);
      }
    }

    this.removeSubscriptionKey(key);
  }

  protected removeClientSubscriptions(client: WebSocket) {
    const subscriptions = this.clientSubscriptions.get(client);
    if (!subscriptions) {
      return;
    }

    subscriptions.forEach((key) => this.removeSubscriptionKey(key));
    this.clientSubscriptions.delete(client);
  }

  protected removeSubscriptionKey(key: string) {
    const record = this.map.get(key);
    if (!record) {
      return;
    }

    record.count -= 1;
    if (record.count <= 0) {
      this.map.delete(key);
    }
  }

  protected getSubscriptionKey(
    api: SDK.ServerAPI.API,
    body: Common.PlainObject | null,
  ) {
    return `${api}:${JSON.stringify(body ?? null)}`;
  }

  protected async getAPIResponse<T extends SDK.ServerAPI.API>(
    api: T,
    body: SDK.ServerAPI.InferRequestBodyType<T>,
  ) {
    const data = await this.loader.loadAPIData(
      api as SDK.ServerAPI.API.LoadDataByKey,
      body as SDK.ServerAPI.InferRequestBodyType<SDK.ServerAPI.API.LoadDataByKey>,
    );
    const response: SDK.ServerAPI.SocketResponseType = {
      req: {
        api,
        body,
      },
      res: data,
    };
    return response;
  }

  protected timer: NodeJS.Immediate | undefined;

  public async broadcast() {
    clearImmediate(this.timer);
    this.timer = setImmediate(async () => {
      const promises: Promise<void>[] = [];

      this.map.forEach(({ api, body }) => {
        promises.push(
          (async () => {
            const res = await this.getAPIResponse(api, body!);
            this.sendAPIData(api, res);
          })(),
        );
      });

      await Promise.all(promises);
    });
  }

  public sendAPIData<T extends SDK.ServerAPI.API | SDK.ServerAPI.APIExtends>(
    api: T,
    payload: SDK.ServerAPI.SocketResponseType<T>,
  ) {
    const message = JSON.stringify({ api, payload });
    this.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

  public dispose() {
    this.clients.forEach((client) => {
      client.close();
    });
    this.clients.clear();
    this.server?.close();
  }
}

```

### packages/types/src/plugin/plugin.ts
```
import { Common, Config, Linter as LinterType, SDK } from '..';
import { InternalRules } from './internal-rules';

export interface RsdoctorRspackPluginFeatures {
  /**
   * Turn it off if you do not need to analyze the executions of bundler loaders.
   * @default true
   */
  loader?: boolean;
  /**
   * Turn it off if you do not need to analyze the executions of bundler plugins.
   * @default true
   */
  plugins?: boolean;
  /**
   * turn off it if you need not to analyze the executions of resolver.
   * @default false
   */
  resolver?: boolean;
  /**
   * turn off it if you need not to analyze the output bundle.
   * @default true
   */
  bundle?: boolean;
  /**
   * Turn it on if you need to analyze tree-shaking side effects.
   * @default false
   */
  treeShaking?: boolean;
  /**
   * turn on it if you just use lite mode. This mode do not have source codes.
   * @default false
   */
  lite?: boolean;
}

export interface RsdoctorPluginOptionsNormalized<
  Rules extends LinterType.ExtendRuleData[] = [],
> extends Common.DeepRequired<
  Omit<
    RsdoctorRspackPluginOptions<Rules>,
    'sdkInstance' | 'linter' | 'output' | 'supports' | 'port' | 'brief' | 'mode'
  >
> {
  features: Common.DeepRequired<RsdoctorRspackPluginFeatures>;
  linter: Required<LinterType.Options<Rules, InternalRules>>;
  sdkInstance?: SDK.RsdoctorBuilderSDKInstance;
  output: {
    mode: keyof typeof SDK.IMode;
    reportCodeType: SDK.ToDataType;
    reportDir: string;
    options: Config.BriefModeOptions | Config.NormalModeOptions;
  };
  port?: number;
  supports: ISupport;
}

interface ISupport {
  parseBundle?: boolean;
  generateTileGraph?: boolean;
  gzip?: boolean;
}

interface OutputBaseConfig {
  /**
   * The directory where the report files will be output.
   */
  reportDir?: string;

  /**
   * Control the Rsdoctor reporter codes records.
   */
  reportCodeType?: IReportCodeType | undefined | NewReportCodeType;

  /**
   * @deprecated
   * Configure whether to compress data.
   * @default false
   *
   */
  compressData?: boolean;
}

export type IReportCodeType = {
  noModuleSource?: boolean;
  noAssetsAndModuleSource?: boolean;
  noCode?: boolean;
};

export type NewReportCodeType =
  | 'noModuleSource'
  | 'noAssetsAndModuleSource'
  | 'noCode';

export interface RsdoctorRspackPluginOptions<
  Rules extends LinterType.ExtendRuleData[],
> {
  /** Checker configuration */
  linter?: LinterType.Options<Rules, InternalRules>;
  /**
   * the switch for the Rsdoctor features.
   */
  features?:
    | RsdoctorRspackPluginFeatures
    | Array<keyof RsdoctorRspackPluginFeatures>;

  /**
   * @deprecated  Use `output.mode` instead, if you're using `lite` mode, please use `output.reportCodeType: 'noCode' or 'noAssetsAndModuleSource'` instead.
   * Rsdoctor mode option:
   * - normal: Refers to the normal mode.
   * - brief: Refers to the brief mode, which only displays the results of the duration analysis and build artifact analysis
   *    and does not display any part of the code.
   */
  mode?: 'brief' | 'normal' | 'lite';

  /**
   * Configuration for the bundler loader interceptor. TODO: delete this option.
   * @description worked when the `features.loader === true`.
   */
  loaderInterceptorOptions?: {
    /**
     * Loaders that should be skipped and not reported when the bundler compiles.
     */
    skipLoaders?: string[];
  };
  /**
   * turn on it if you don't need to see profile in browser.
   * @default false
   */
  disableClientServer?: boolean;

  /**
   * sdk instance of outside.
   */
  sdkInstance?: SDK.RsdoctorBuilderSDKInstance;

  /** Whether to turn on specific analysis capabilities. */
  supports?: ISupport;

  /**
   * The port of the Rsdoctor server.
   */
  port?: number;

  /**
   * Options to control the log printing.
   */
  printLog?: SDK.IPrintLog;

  /**
   * @deprecated  Use `output.options.htmlOptions` instead.
   * Please use the output.options to set the brief options, BriefModeOptions.
   * Options to control brief mode reports.
   */
  brief?: Config.BriefConfig;

  /**
   * The name of inner rsdoctor's client package, used by inner-rsdoctor.
   * @default false
   */
  innerClientPath?: string;

  output?: Config.IOutput<'brief' | 'normal'>;
}

// Conditional type for reportCodeType based on mode
type ReportCodeTypeByMode<T extends 'brief' | 'normal'> = T extends 'brief'
  ? undefined | 'noCode' | { noCode?: boolean }
  : T extends 'normal'
    ? IReportCodeType | undefined | NewReportCodeType
    : IReportCodeType | undefined | NewReportCodeType;

export interface NormalModeOptions {
  // Normal mode doesn't have type field, it's only available in brief mode
  type?: never;
}

// Normal Mode Type
interface NormalModeConfig extends Omit<
  OutputBaseConfig,
  'reportCodeType' | 'mode'
> {
  mode?: 'normal';
  reportCodeType?: ReportCodeTypeByMode<'normal'>;
  options?: NormalModeOptions;
}

export interface BriefModeOptions {
  /** Output type, supports HTML and JSON */
  type?: Array<'html'>;
  /** HTML output related configuration */
  // jsonOptions?: {};
  htmlOptions?: Config.BriefConfig;
}

export interface BriefModeConfig extends Omit<
  OutputBaseConfig,
  'reportCodeType' | 'mode'
> {
  mode?: 'brief';
  reportCodeType?: ReportCodeTypeByMode<'brief'>;
  options?: BriefModeOptions;
}

export type IOutput<T extends 'brief' | 'normal' | undefined = undefined> =
  T extends 'brief'
    ? BriefModeConfig
    : T extends 'normal'
      ? NormalModeConfig
      : BriefModeConfig | NormalModeConfig | OutputBaseConfig;

```

### packages/types/src/sdk/instance.ts
```
import type { SourceMapConsumer, RawSourceMap } from 'source-map';

import { LoaderData, ResourceLoaderData } from './loader';
import { ResolverData } from './resolver';
import { PluginData } from './plugin';
import { BuilderStoreData, EMOStoreData } from './result';
import { ModuleGraphInstance, ToDataType } from './module';
import {
  RsdoctorManifestClientRoutes,
  RsdoctorManifestWithShardingFiles,
} from '../manifest';
import { RuntimeContext, RuntimeContextOptions } from './context';
import { Hooks } from './hooks';
import { ChunkGraphInstance } from './chunk';
import { RsdoctorServerInstance } from './server';
import { PlainObject } from '../common';
import { BriefModeOptions } from '../config';
import { EmoCheckData } from '../emo';
import { SummaryData } from './summary';
import { ConfigData } from './config';

// rslint-disable-next-line @typescript-eslint/no-empty-object-type
export type WriteStoreOptionsType = {};

export enum IMode {
  brief = 'brief',
  lite = 'lite',
  normal = 'normal',
}

export interface RsdoctorBuilderSDKInstance extends RsdoctorSDKInstance {
  readonly server: RsdoctorServerInstance;
  type: ToDataType;

  /** Report configuration information */
  reportConfiguration(config: ConfigData[0]): void;

  /** Report error message */
  reportError(errors: Error[]): void;
  /** Report error message */
  reportLoader(data: LoaderData): void;
  /** Report loader message before or after some builtin loader */
  reportLoaderStartOrEnd(data: ResourceLoaderData): void;
  /** Report path request information */
  reportResolver(data: ResolverData): void;
  /** Report plugin information */
  reportPlugin(data: PluginData): void;
  /** Report module chart data */
  reportModuleGraph(data: ModuleGraphInstance): void;
  reportChunkGraph(data: ChunkGraphInstance): void;
  /** report the data of summary */
  reportSummaryData(part: Partial<SummaryData>): void;
  /** Report sourceMap data */
  reportSourceMap(data: RawSourceMap): void;

  getClientRoutes(): RsdoctorManifestClientRoutes[];
  addClientRoutes(routes: RsdoctorManifestClientRoutes[]): void;

  /** Application error modification */
  applyErrorFix(id: number): Promise<void>;
  /** Get build result data */
  getStoreData(): BuilderStoreData;
  /** Get build resource entry file */
  getManifestData(): RsdoctorManifestWithShardingFiles;
  /** Get rule context */
  getRuleContext(options: RuntimeContextOptions): RuntimeContext;
  /** Get SourceMap from cache */
  getSourceMap(file: string): Promise<SourceMapConsumer | undefined>;
  /** clear cache */
  clearSourceMapCache(): void;
  /** Clear all data */
  clear(): void;
  /** Write store data to files */
  writeStore(options?: WriteStoreOptionsType): Promise<string>;
}

export interface RsdoctorEMOSDKInstance extends RsdoctorSDKInstance {
  reportEmoData(data: EmoCheckData): void;
  getStoreData(): EMOStoreData;
}

export interface RsdoctorSDKInstance {
  readonly name: string;
  readonly root: string;
  readonly extraConfig: SDKOptionsType | undefined;
  readonly hooks: Hooks;

  /**
   * folder of manifest
   *   - used to save the manifest.json and sharding files.
   * @default ".rsdoctor"
   */
  readonly outputDir: string;

  /** manifest local path */
  diskManifestPath: string;

  /** start */
  bootstrap(): Promise<void>;
  dispose(): Promise<void>;

  /** Change output path */
  setOutputDir(outputDir: string): void;

  /** Change build name */
  setName(name: string): void;
  setHash(hash: string): void;
  getHash(): string;

  /**
   * write the manifest to a folder
   *   - use this.outputDir
   * @returns the absolute path of manifest.json.
   */
  saveManifest(
    storeData: PlainObject,
    options: WriteStoreOptionsType,
  ): Promise<string>;
}

export interface IPrintLog {
  serverUrls: boolean;
}

export type SDKOptionsType = {
  innerClientPath?: string;
  disableClientServer?: boolean;
  noServer?: boolean;
  printLog?: IPrintLog;
  mode?: keyof typeof IMode;
  brief?: BriefModeOptions;
  features?: { treeShaking?: boolean };
};

```

### packages/types/src/sdk/server/index.ts
```
import { PlainObject } from '../../common';
import { connect } from '../../thirdparty';
import { RsdoctorClientRoutes } from '../../client';
import { API, APIExtends } from './apis';

export * as ServerAPI from './apis';

interface ClientUrlFunctionWithRouteDefined<T> {
  (
    route: RsdoctorClientRoutes.BundleDiff,
    baselineUrl: string,
    currentUrl: string,
  ): T;
  (route?: 'homepage'): T;
}

export interface RsdoctorServerInstance {
  readonly app: connect.Server;

  readonly port: number;
  readonly origin: string;

  innerClientPath?: string;

  get(
    route: string,
    cb: (
      ...args: Parameters<connect.NextHandleFunction>
    ) => string | PlainObject,
  ): connect.Server;
  post(
    route: string,
    cb: (
      ...args: Parameters<connect.NextHandleFunction>
    ) => string | PlainObject,
  ): connect.Server;

  proxy(
    route: string,
    method: 'GET' | 'POST',
    cb: (
      ...args: Parameters<connect.NextHandleFunction>
    ) => PlainObject | string,
  ): void;

  getClientUrl: ClientUrlFunctionWithRouteDefined<string>;

  openClientPage: ClientUrlFunctionWithRouteDefined<Promise<void>>;

  sendAPIDataToClient(api: API | APIExtends, msg: unknown): void | never;

  broadcast(): void;

  bootstrap(): Promise<void>;
  dispose(): Promise<void>;
}

```

### packages/utils/src/common/global-config.ts
```
import fs from 'fs';
import path from 'path';
import os from 'os';
import { logger } from '../logger';

/**
 * @description Writes the builder port information to mcp.json.
 *
 * The mcp.json file uses the following format:
 * {
 *   portList: {
 *     builder1: portNumber,
 *     builder2: portNumber,
 *   },
 *   port: portNumber // The port of the last builder is used by default
 * }
 *
 * @param {number} port - The port number to write.
 * @param {string} [builderName] - The name of the builder.
 */
export function writeMcpPort(port: number, builderName?: string) {
  const homeDir = os.homedir();
  const rsdoctorDir = path.join(homeDir, '.cache/rsdoctor');
  const mcpPortFilePath = path.join(rsdoctorDir, 'mcp.json');

  if (!fs.existsSync(rsdoctorDir)) {
    fs.mkdirSync(rsdoctorDir, { recursive: true });
  }

  let mcpJson: { portList: Record<string, number>; port: number } = {
    portList: {},
    port: 0,
  };

  if (fs.existsSync(mcpPortFilePath)) {
    try {
      mcpJson = JSON.parse(fs.readFileSync(mcpPortFilePath, 'utf8'));
    } catch (error) {
      logger.debug('Failed to parse mcp.json', error);
    }
  }

  if (!mcpJson.portList) mcpJson.portList = {};
  mcpJson.portList[builderName || 'builder'] = port;

  // Use the latest generated port.
  mcpJson.port = port;

  fs.writeFileSync(mcpPortFilePath, JSON.stringify(mcpJson, null, 2), 'utf8');
}

/**
 * @description Gets the path to the mcp.json file.
 * @returns {string} The path to the mcp.json file.
 */
export function getMcpConfigPath() {
  const homeDir = os.homedir();
  const rsdoctorDir = path.join(homeDir, '.cache/rsdoctor');
  const mcpPortFilePath = path.join(rsdoctorDir, 'mcp.json');
  return mcpPortFilePath;
}

```
Callers & Entry Points (How public input reaches the modified code)
### packages/types/src/sdk/index.ts
```
export * from './loader';
export * from './resolver';
export * from './plugin';
export * from './module';
export * from './chunk';
export * from './result';
export * from './summary';
export * from './package';
export * from './context';
export * from './config';
export * from './server';
export * from './statement';
export * from './treeShaking';
export * from './envinfo';
export * from './instance';
export * from './hooks';

```

### packages/core/src/inner-plugins/utils/index.ts
```
export * from './loader';
export * from './plugin';
export * from './sdk';
export * from './config';
export * from './circleDetect';
export * from './plugin-common';
export * from './normalize-config';
export * from './plugin-common';
export * from './normalize-config';

```

### packages/types/src/index.ts
```
export * as Manifest from './manifest';
export * as Esbuild from './esbuild';
export * as Babel from './babel';
export * as Common from './common';

export * as Err from './error';
export * as Logger from './logger';
export * as SDK from './sdk';
export * as Modules from './modules';
export * as Linter from './linter';

export * as Rule from './rule';
export * as Thirdparty from './thirdparty';

export * as Client from './client';
export * as Constants from './constants';

export * as Plugin from './plugin';
export * as Config from './config';

```

### packages/types/src/sdk/server/apis/index.ts
```
import { ServerResponse } from 'http';
import { PlainObject, Get } from '../../../common';
import { connect } from '../../../thirdparty';
import { RsdoctorBuilderSDKInstance } from '../../index';
import { RsdoctorServerInstance } from '../index';
import { LoaderData } from '../../loader';
import { ProjectAPIResponse, ProjectAPIRequestBody } from './project';
import { LoaderAPIResponse, LoaderAPIRequestBody } from './loader';
import { ResolverAPIResponse, ResolverAPIRequestBody } from './resolver';
import { PluginAPIResponse, PluginAPIRequestBody } from './plugin';
import { GraphAPIResponse, GraphAPIRequestBody } from './graph';
import { AlertsAPIResponse, AlertsAPIRequestBody } from './alerts';
import { RsdoctorManifestMappingKeys } from '../../../manifest';
import { SDK } from '../../../index';
import { StatsModule } from '../../../plugin';

export * from './pagination';

export enum API {
  ApplyErrorFix = '/api/apply/error/fix',
  Env = '/api/env',
  EntryHtml = '/index.html',
  Manifest = '/api/manifest.json',

  LoadDataByKey = '/api/data/key',

  SendAPIDataToClient = '/api/socket/send',

  /** Project API */
  GetProjectInfo = '/api/project/info',
  GetClientRoutes = '/api/routes',

  /** Loader API */
  ReportLoader = '/api/loader/report',
  GetLoaderNames = '/api/loader/names',
  GetLoaderChartData = '/api/loader/chart/data',
  GetLoaderFileTree = '/api/loader/filetree',
  GetLoaderFileDetails = '/api/loader/file',
  GetLoaderFolderStatistics = '/api/loader/folder/statics',
  GetLoaderFileFirstInput = '/api/loader/input',
  GetLoaderFileInputAndOutput = '/api/loader/inputandoutput',
  GetDirectoriesLoaders = '/api/loader/directories',

  /** SourceMap API */
  ReportSourceMap = '/api/sourcemap/report',

  /** Resolver API */
  GetResolverFileTree = '/api/resolver/filetree',
  GetResolverFileDetails = '/api/resolver/file',

  /** Plugin API */
  GetPluginSummary = '/api/plugins/summary',
  GetPluginData = '/api/plugins/data',

  /** Graph API */
  GetSummaryBundles = '/api/graph/bundles/summary',
  GetChunkGraph = '/api/graph/chunks/graph',
  GetAssetsSummary = '/api/graph/assets/summary',
  GetAssetDetails = '/api/graph/asset/details',
  GetChunksByModuleId = '/api/graph/chunk/module',
  GetModuleDetails = '/api/graph/module/details',
  GetModulesByModuleIds = '/api/graph/modules/ids',
  GetEntryPoints = '/api/graph/entrypoints',
  GetModuleCodeByModuleId = '/api/graph/module/code',
  GetModuleCodeByModuleIds = '/api/graph/module/codes',
  GetAllModuleGraph = '/api/graph/module/all',
  GetAllChunkGraph = '/api/graph/chunk/all',
  GetLayers = '/api/graph/layers',
  GetSearchModules = '/api/search/modules',
  GetSearchModuleInChunk = '/api/search/chunk/modules',
  GetAllModuleGraphFilter = '/api/graph/module/filter',
  GetModuleByName = '/api/graph/module/name',
  GetModuleIssuerPath = '/api/graph/module/issuer_path',

  /** Package API */
  GetPackageInfo = '/api/package/info',
  GetPackageDependency = '/api/package/dependency',

  /** Alerts API */
  GetPackageRelationAlertDetails = '/api/alerts/details/package/relation',
  GetOverlayAlerts = '/api/alerts/overlay',
  GetBundleAlerts = '/api/alerts/bundle',

  /** BundleDiff API */
  BundleDiffManifest = '/api/bundle_diff/manifest.json',
  GetBundleDiffSummary = '/api/bundle_diff/summary',

  /** AI API */
  GetChunkGraphAI = '/api/graph/chunks/graph/ai',
  GetChunkByIdAI = '/api/graph/chunk/id/ai',
}

/**
 * api which used outside the sdk.
 */
export enum APIExtends {
  GetCompileProgress = '/api/progress',
}

export interface SocketResponseType<T extends API | APIExtends = API> {
  /**
   * use to match for the event listener when there are different request body.
   */
  req: {
    api: T;
    body: InferRequestBodyType<T>;
  };
  /**
   * api response
   */
  res: InferResponseType<T>;
}

export interface ResponseTypes
  extends
    LoaderAPIResponse,
    ResolverAPIResponse,
    PluginAPIResponse,
    GraphAPIResponse,
    AlertsAPIResponse,
    ProjectAPIResponse {
  [API.ReportLoader]: 'ok';
  [API.EntryHtml]: string;
  [API.Manifest]: string;
  [API.ApplyErrorFix]: 'success';
  [API.LoadDataByKey]: unknown;
  [API.BundleDiffManifest]: SDK.BuilderStoreData;
  [API.GetBundleDiffSummary]: {
    root: string;
    hash: string;
    outputFilename: string;
    errors: SDK.ErrorsData;
    chunkGraph: SDK.ChunkGraphData;
    moduleGraph: SDK.ModuleGraphData;
    packageGraph: SDK.PackageGraphData;
    moduleCodeMap: SDK.ModuleCodeData;
    cloudManifestUrl: string;
  };
  [API.GetChunkGraph]: SDK.ChunkData[];
  [API.GetAllModuleGraphFilter]: SDK.ModuleData[];
  [API.GetModuleCodeByModuleId]: SDK.ModuleSource;
  [API.GetModuleCodeByModuleIds]: SDK.ModuleCodeData;
  [API.GetAllModuleGraph]: SDK.ModuleData[];
  [API.GetSearchModules]: Record<string, string>;
  [API.GetSearchModuleInChunk]: {
    id: string;
    path: string;
    relativePath: string;
  }[];
  [API.GetAllChunkGraph]: SDK.ChunkData[];
  [API.GetModuleByName]: { id: number; path: string }[];
  [API.GetModuleIssuerPath]: StatsModule['issuerPath'];
  [API.GetPackageInfo]: SDK.PackageData[];
  [API.GetPackageDependency]: SDK.PackageDependencyData[];
  [API.GetChunkByIdAI]: ExtendedChunkData[];
  [API.GetChunkGraphAI]: Omit<SDK.ChunkData, 'modules'>[];
  [API.GetSummaryBundles]: {
    asset: SDK.AssetData;
    modules: SDK.ModuleData[];
  }[];
}

export interface RequestBodyTypes
  extends
    LoaderAPIRequestBody,
    ResolverAPIRequestBody,
    PluginAPIRequestBody,
    GraphAPIRequestBody,
    AlertsAPIRequestBody,
    ProjectAPIRequestBody {
  [API.ReportLoader]: LoaderData;
  [API.ApplyErrorFix]: { id: number };
  [API.SendAPIDataToClient]: {
    api: API;
    data: unknown;
  };
  [API.LoadDataByKey]: {
    /**
     * @example 'plugin'
     * @example 'moduleGraph.modules'
     */
    key: RsdoctorManifestMappingKeys;
  };
  [API.GetModuleByName]: {
    moduleName: string;
  };
  [API.GetModuleIssuerPath]: {
    moduleId: string;
  };
  [API.GetPackageDependency]: {
    packageId: string;
  };
  [API.GetChunkByIdAI]: {
    chunkId: string;
  };
}

export type InferResponseType<T, F = void> = Get<ResponseTypes, T, F>;

export type InferRequestBodyType<T, F = void> = Get<RequestBodyTypes, T, F>;

export interface APIContext {
  server: RsdoctorServerInstance;
  sdk: RsdoctorBuilderSDKInstance;
  req: connect.IncomingMessage & { body?: PlainObject };
  res: ServerResponse;
}

export interface ExtendedChunkData extends SDK.ChunkData {
  modulesInfo: {
    id: number;
    path: string;
    size: SDK.ModuleSize;
    chunks: string[];
    kind: SDK.ModuleKind;
    issuerPath: string[] | number[] | undefined;
  }[];
}

```

### packages/rspack-plugin/src/index.ts
```
export * from './plugin';
export * from './multiple';

```

### packages/utils/src/common/index.ts
```
export * as Summary from './summary';
export * as Crypto from './crypto';
export * as Manifest from './manifest';
export * as Loader from './loader';
export * as Time from './time';
export * as Algorithm from './algorithm';
export * as Resolver from './resolver';
export * as Graph from './graph';
export * as Bundle from './bundle';
export * as Url from './url';
export * as Plugin from './plugin';
export * as Data from './data';
export * as Alerts from './alerts';
export * as Fetch from './fetch';
export * as Rspack from './rspack';
export * as Package from './package';
export * as Lodash from './lodash';
export * as GlobalConfig from './global-config';
export * as File from './file';
export * from './decycle';

```

### packages/types/src/sdk/module.ts
```
import type { Program } from 'estree';
import type { SourceMapConsumer } from 'source-map';
import type { NonFunctionProperties } from '../common';
import type { ChunkInstance } from './chunk';
import type { BriefModeOptions } from '../config';
import type { StatementInstance, StatementData } from './statement';
import type { PackageData } from './package';
import type {
  ModuleGraphModuleInstance,
  ModuleGraphModuleData,
  ExportData,
  ExportInstance,
  SideEffectData,
  SideEffectInstance,
  VariableData,
  VariableInstance,
} from './treeShaking';
import type { StatsModule } from '../plugin';

export enum DependencyKind {
  Unknown,
  ImportStatement,
  DynamicImport,
  RequireCall,
  AMDRequire,
}

/** Source code location */
export interface SourcePosition {
  line?: number;
  column?: number;
  index?: number;
}

/** Source code range */
export interface SourceRange {
  start: SourcePosition;
  end?: SourcePosition;
}

/** Side effect location from bundler (e.g. Rspack JsRsdoctorSideEffectLocation) */
export interface SideEffectLocationData {
  location: string;
  nodeType: string;
  module: number;
  request: string;
}

/** Pre-computed side-effects-only import result (from Rust analysis) */
export interface ConnectionsOnlyImportData {
  moduleUkey: number;
  modulePath: string;
  connections: Array<{
    originModule?: number;
    dependencyType: string;
    userRequest: string;
  }>;
}

/** Side effect code snippet data */
export interface SideEffectCodeData {
  /** Module ID */
  moduleId: number;
  /** Start line number (1-indexed) */
  startLine: number;
  /** Extracted source code snippet */
  code: string;
}

/** Module size */
export interface ModuleSize {
  sourceSize: number;
  /** Code size after transformed */
  transformedSize: number;
  /**
   * Code size after compiled
   *   - The size the module occupies in the product after packing.
   */
  parsedSize: number;
  /**
   * Gzipped size of the module source (optional)
   */
  gzipSize: number;
}

/** Module source code */
export interface ModuleSource {
  /** source code */
  source: string;
  /** transformed code */
  transformed: string;
  /* code after parsed */
  parsedSource: string;
}

/** Module Metadata */
export interface ModuleBuildMeta {
  /**
   * Whether to include the esModule flag statement
   * ```js
   * Object.defineProperty(exports, "__esModule", { value: true });
   * ```
   *   - This statement usually appears in the object code of the tsc to cjs module.
   */
  hasSetEsModuleStatement: boolean;
  /**
   * Strict ESM module.
   */
  strictHarmonyModule: boolean;
  packageData?: PackageData;
}

/** Module type */
export enum ModuleKind {
  /** Normal module */
  Normal,
  /** Aggregation module */
  Concatenation,
}

export enum ToDataType {
  NoCode,
  /** Normal mode */
  Normal,
  /** Lite mode: no source code */
  NoSource,
  /** Lite & No Assets Code mode */
  NoSourceAndAssets,
  /** All Data, include module transformed data. */
  All,
}

export interface ModuleInstance {
  /** Module identifier */
  readonly id: number;
  /** Bundler render identifier */
  readonly renderId?: string;
  /** Bundler identifier */
  readonly identifier: string;
  /** Module path */
  readonly path: string;
  readonly isEntry: boolean;
  readonly kind: ModuleKind;
  /** Root module in aggregate module */
  readonly rootModule?: ModuleInstance;
  readonly layer?: string;
  /**
   * Preference to source location
   *   - Indicates that the source code is not empty and there is source code location mapping data.
   */
  isPreferSource: boolean;
  /** Build properties */
  meta: ModuleBuildMeta;

  /** Issuer paths */
  issuerPath?: StatsModule['issuerPath'];

  bailoutReason?: string[];

  /** Get the Chunks instance where the module in.*/
  getChunks(): ChunkInstance[];
  /** Add Chunk instance */
  addChunk(chunk: ChunkInstance): void;
  removeChunk(chunk: ChunkInstance): void;
  getDependencies(): DependencyInstance[];
  getDependencyByRequest(request: string): DependencyInstance | undefined;
  /** Get dependency data from module */
  getDependencyByModule(module: ModuleInstance): DependencyInstance | undefined;
  removeDependency(dependency: DependencyInstance): void;
  /** Remove dependency data from module */
  removeDependencyByModule(module: ModuleInstance): void;
  removeImported(module: ModuleInstance): void;
  getImported(): ModuleInstance[];
  addImported(module: ModuleInstance): void;
  addDependency(
    request: string,
    module: ModuleInstance,
    kind: DependencyKind,
    statements?: StatementInstance[],
  ): DependencyInstance | undefined;
  toData(contextPath?: string, isBrief?: boolean): ModuleData;
  setSource(source: Partial<ModuleSource>): void;
  getSource(type?: ToDataType): ModuleSource;
  /**Set code AST after transform */
  setProgram(program: Program): void;
  /** Get the converted code AST */
  getProgram(): Program | undefined;
  /** Set module size information */
  setSize(size: Partial<ModuleSize>): void;
  getSize(): ModuleSize;
  setSourceMap(sourcemap: SourceMapConsumer): void;
  /** Get source code mapping */
  getSourceMap(): SourceMapConsumer | undefined;
  /**
   * Generate statement instances
   * @param transformed {SourceRange} The location of the transformed code.
   */
  getStatement(transformed: SourceRange): StatementInstance | undefined;
  /**
   * Generate original code location
   * @param transformed {SourceRange} The location of the transformed code.
   */
  getSourceRange(transformed: SourceRange): SourceRange | undefined;
  /** Add connected submodules */
  addNormalModule(module: ModuleInstance): void;
  /** If it is currently a connection module, return all connected base sub packages */
  getNormalModules(): ModuleInstance[];
  /** Added aggregation module */
  addConcatenationModule(module: ModuleInstance): void;
  /** Get all aggregated modules to which the current module belongs */
  getConcatenationModules(): ModuleInstance[];

  setId(id: number): void;
  setChunks(chunks: ChunkInstance[]): void;
  setDependencies(dependencies: DependencyInstance[]): void;
  setImported(imported: ModuleInstance[]): void;
  setModules(modules: ModuleInstance[]): void;
  setConcatenationModules(modules: ModuleInstance[]): void;
  setRenderId(renderId: string): void;
  /** Add an issuer path */
  addIssuerPath(issuerPath: StatsModule['issuerPath']): void;
  /** Get issuer path */
  getIssuerPath(): StatsModule['issuerPath'];
  /** Add bailout reason */
  addBailoutReason(reason: string): void;
  /** Get bailout reason */
  getBailoutReason(): string[];
  /** Side effect location data (e.g. from Rspack sideEffectsLocations) */
  sideEffectLocations?: SideEffectLocationData[];
  /** Add a side effect location */
  addSideEffectLocation(location: SideEffectLocationData): void;
  /** Get side effect locations */
  getSideEffectLocations(): SideEffectLocationData[];
  /** Add side effect code */
  addSideEffectCode(codeData: SideEffectCodeData): void;
  /** Get side effect codes */
  getSideEffectCodes(): SideEffectCodeData[];
}

/** Depends on Metadata */
export interface DependencyBuildMeta {
  /**
   * Types of dependencies between modules
   *   - The basis for the bundler to add runtime to modules.
   */
  exportsType: 'namespace' | 'default-only' | 'default-with-named' | 'dynamic';
}

export interface DependencyInstance {
  /** Identifier */
  readonly id: number;
  /**
   * Original request
   *  - refers to the original request in the import statement
   *  - @example `import {Instance} from'chalk'` in the statement 'chalk'
   */
  readonly request: string;
  /** actual requested path */
  readonly resolvedRequest: string;
  /** Module */
  readonly module: ModuleInstance;
  /**
   * Dependency Module
   * - Always non-aggregated modules
   */
  readonly dependency: ModuleInstance;
  /**
   * Original dependency module
   * - Aggregation module preferred
   */
  readonly originDependency: ModuleInstance;
  /**
   * Citation method
   * - Numeric enumeration
   */
  readonly kind: DependencyKind;
  /**
   * Citation method
   * - string enumeration
   */
  readonly kindString: keyof typeof DependencyKind;
  /**
   * Original dependency type string from the bundler (e.g. 'cjs require', 'cjs full require', 'esm import')
   */
  typeString?: string;
  /** Whether to connect to the aggregation module */
  readonly resolveConcatenationModule: boolean;
  /** quote statement */
  readonly statements: StatementInstance[];
  /** build attribute */
  meta: DependencyBuildMeta;
  /** Generate data */
  toData(): DependencyData;
  /** Add statement */
  addStatement(statement: StatementInstance): void;
  /** Whether this statement is included */
  hasStatement(statement: StatementInstance): boolean;
  /**
   * Is it the same dependency?
   * - Check properties other than id and statements
   */
  isSameWithoutStatements(dep: DependencyInstance): boolean;

  setBuildMeta(data: DependencyBuildMeta): void;
  setId(id: number): void;
}

export type ModuleGraphToDataArgs = {
  contextPath: string;
  briefOptions?: BriefModeOptions;
};

export interface ModuleGraphInstance {
  /** Clear data */
  clear(): void;

  /** How many modules are there in total */
  size(): number;

  /** overwrite data */
  fromInstance(data: ModuleGraphInstance): void;

  /** Create module connection data */
  addModuleGraphModule(info: ModuleGraphModuleInstance): void;

  /** Get module connection data */
  getModuleGraphModule(module: ModuleInstance): ModuleGraphModuleInstance;

  /** Get all module connection data */
  getModuleGraphModules(): ModuleGraphModuleInstance[];

  /** Get all modules */
  getModules(): ModuleInstance[];

  /** Get all modules */
  getDependencies(): DependencyInstance[];

  /** Get connection by id */
  getDependencyById(id: number): DependencyInstance | undefined;

  /** Get entrance module */
  getEntryModules(): ModuleInstance[];

  /** Get the subgraph of the current node as the entry point */
  getSubGraphByModule(module: ModuleInstance): ModuleInstance[];

  /** Get module by id */
  getModuleById(id: number): ModuleInstance | undefined;

  /** get module by identifier */
  getModuleByIdentifier(identifier: string): ModuleInstance | undefined;

  /** Get module by path */
  getModuleByFile(file: string, layer?: string): ModuleInstance[] | [];

  /** Add Module */
  addModule(module: ModuleInstance): void;

  /** Add module connection */
  addDependency(module: DependencyInstance): void;
  /**
   * Remove module
   * - The connection relationship of this module will also be removed
   */
  removeModule(module: ModuleInstance): void;
  /**
   * Remove connection
   * - If one of the connected endpoints is an independent module, this module will also be removed from the module diagram
   */
  removeDependency(dependency: DependencyInstance): void;
  /** Add export data */
  addExportInfo(data: ExportInstance): void;

  /** Add side effect data */
  addSideEffect(data: SideEffectInstance): void;

  /** Add variable data */
  addVariable(data: VariableInstance): void;

  /** Generate data */
  toData(configs?: ModuleGraphToDataArgs): ModuleGraphData;

  /** Generate tree shaking data */
  toTreeShakingData(): TreeShakingData;

  /** Generate data */
  toCodeData(type?: ToDataType): ModuleCodeData;

  setModules(modules: ModuleInstance[]): void;
  setDependencies(dependencies: DependencyInstance[]): void;
  setConnectionsOnlyImports(items: ConnectionsOnlyImportData[]): void;
  getConnectionsOnlyImports(): ConnectionsOnlyImportData[];
}

export interface ModuleData extends Omit<
  NonFunctionProperties<ModuleInstance>,
  'rootModule' | 'isEntry' | 'concatenationModules' | 'meta' | 'issuerPath'
> {
  /** chunk identifier */
  chunks: string[];

  /** Module identifier on which the module depends */
  dependencies: number[];

  /** Identifier of the dependent module */
  imported: number[];

  /** Is it an entrance module */
  isEntry?: boolean | undefined;

... [truncated]
```

### packages/sdk/src/sdk/index.ts
```
export * from './sdk';
export * from './multiple';

```

### packages/types/src/sdk/result.ts
```
import { EmoCheckData } from '../emo';
import { LoaderData } from './loader';
import { ModuleGraphData, ModuleCodeData, TreeShakingData } from './module';
import { ChunkGraphData } from './chunk';
import { ResolverData } from './resolver';
import { PluginData } from './plugin';
import { SummaryData } from './summary';
import { ConfigData } from './config';
import { RuleStoreData } from '../rule';
import type { EnvInfo } from './envinfo';
import { PackageGraphData, OtherReports } from './package';

export type ErrorsData = RuleStoreData;

interface StoreCommonData {
  hash: string;
  root: string;
  pid: number;
  envinfo: EnvInfo;
}

export interface BuilderStoreData extends StoreCommonData {
  [key: string]: any;
  errors: ErrorsData;
  configs: ConfigData;
  summary: SummaryData;
  resolver: ResolverData;
  loader: LoaderData;
  plugin: PluginData;
  moduleGraph: ModuleGraphData;
  chunkGraph: ChunkGraphData;
  packageGraph: PackageGraphData;
  moduleCodeMap: ModuleCodeData;
  treeShaking?: TreeShakingData;
  otherReports?: OtherReports | undefined;
}

export interface EMOStoreData extends StoreCommonData {
  emoCheck: EmoCheckData;
}

/**
 * @deprecated
 */
export interface StoreData
  extends Partial<Omit<EMOStoreData, keyof StoreCommonData>>,
    BuilderStoreData {}

```

### packages/core/src/types/plugin.ts
```
import type { RsdoctorPrimarySDK } from '@rsdoctor/sdk';
import type {
  Linter,
  Linter as LinterType,
  Plugin,
  SDK,
} from '@rsdoctor/types';
export interface RsdoctorMultiplePluginOptions<
  Rules extends LinterType.ExtendRuleData[] = LinterType.ExtendRuleData[],
>
  extends
    Omit<Plugin.RsdoctorRspackPluginOptions<Rules>, 'sdkInstance'>,
    Pick<ConstructorParameters<typeof RsdoctorPrimarySDK>[0], 'stage'> {
  /**
   * name of builder
   */
  name?: string;
}

export interface BasePluginInstance<T extends Plugin.BaseCompiler> {
  apply: (compiler: T) => void;
  [k: string]: any;
}

export interface InternalPlugin<
  T extends Plugin.BaseCompiler,
  Rules extends LinterType.ExtendRuleData[] = [],
> extends BasePluginInstance<T> {
  readonly name: string;
  readonly scheduler: RsdoctorPluginInstance<T, Rules>;
}

export interface RsdoctorPluginInstance<
  T extends Plugin.BaseCompiler,
  Rules extends LinterType.ExtendRuleData[] = [],
> extends BasePluginInstance<T> {
  readonly name: string;
  readonly options: Plugin.RsdoctorPluginOptionsNormalized<Rules>;
  readonly sdk: SDK.RsdoctorBuilderSDKInstance;
  readonly isRsdoctorPlugin: boolean;
  _modulesGraphApplied?: boolean;
  chunkGraph?: SDK.ChunkGraphInstance;
  modulesGraph: SDK.ModuleGraphInstance;
  ensureModulesChunksGraphApplied(compiler: T): void;
}

export type RsdoctorRspackPluginInstance<
  Rules extends LinterType.ExtendRuleData[] = [],
> = RsdoctorPluginInstance<Plugin.BaseCompilerType<'rspack'>, Rules>;

export interface NativePluginConfig {
  moduleGraph?: boolean;
  chunkGraph?: boolean;
}

export interface RsdoctorRspackPluginExperiments {
  /**
   * Whether to enable the native plugin to improve the performance.
   * @default true
   */
  enableNativePlugin?: boolean;
}

export interface RsdoctorRspackPluginExperimentsNormalized {
  enableNativePlugin?: NativePluginConfig;
}

export interface RsdoctorRspackPluginOptions<
  Rules extends LinterType.ExtendRuleData[],
> extends Plugin.RsdoctorRspackPluginOptions<Rules> {
  /**
   * The experiments of the Rsdoctor Rspack plugin.
   */
  experiments?: RsdoctorRspackPluginExperiments;
}

export type RsdoctorRspackPluginOptionsNormalized<
  Rules extends Linter.ExtendRuleData[],
> = Plugin.RsdoctorPluginOptionsNormalized<Rules> & {
  experiments?: RsdoctorRspackPluginExperimentsNormalized;
};

```

### packages/cli/src/index.ts
```
import { cac } from 'cac';
import { red } from 'picocolors';
import { Common } from '@rsdoctor/types';
import { analyze, bundleDiff } from './commands';
import { Command, CommandContext, GetCommandArgumentsType } from './types';
import { Commands, pkg, bin } from './constants';
import { logger } from '@rsdoctor/utils/logger';
import { statsAnalyze } from './commands/stats-analyze';

interface AnalyzeArgs {
  profile: string;
  open?: boolean;
  port?: number;
  type?: string;
}

interface BundleDiffArgs {
  current: string;
  baseline: string;
  open?: boolean;
}

interface StatsAnalyzeArgs {
  profile: string;
  open?: boolean;
  port?: number;
  type?: string;
}

type CommandArgs = AnalyzeArgs | BundleDiffArgs | StatsAnalyzeArgs;

function isAnalyzeCommand(command: string): command is Commands.Analyze {
  return command === Commands.Analyze;
}

function isBundleDiffCommand(command: string): command is Commands.BundleDiff {
  return command === Commands.BundleDiff;
}

function isStatsAnalyzeCommand(
  command: string,
): command is Commands.StatsAnalyze {
  return command === Commands.StatsAnalyze;
}

// Validation function with proper typing
function validateRequiredArgs(command: string, args: CommandArgs): void {
  if (isAnalyzeCommand(command)) {
    const analyzeArgs = args as AnalyzeArgs;
    if (!analyzeArgs.profile) {
      logger.error(red(`❌ Missing required argument: --profile`));
      logger.info(`💡 Usage: ${bin} ${command} --profile <path>`);
      logger.info(`💡 Use --help to see all available options`);
      process.exit(1);
    }
  }

  if (isBundleDiffCommand(command)) {
    const bundleDiffArgs = args as BundleDiffArgs;
    if (!bundleDiffArgs.current || !bundleDiffArgs.baseline) {
      logger.error(
        red(`❌ Missing required arguments: --current and --baseline`),
      );
      logger.info(
        `💡 Usage: ${bin} ${command} --current <path> --baseline <path>`,
      );
      logger.info(`💡 Use --help to see all available options`);
      process.exit(1);
    }
  }

  if (isStatsAnalyzeCommand(command)) {
    const statsAnalyzeArgs = args as StatsAnalyzeArgs;
    if (!statsAnalyzeArgs.profile) {
      logger.error(red(`❌ Missing required argument: --profile`));
      logger.info(`💡 Usage: ${bin} ${command} --profile <path>`);
      logger.info(`💡 Use --help to see all available options`);
      process.exit(1);
    }
  }
}

// Error handling function for cac errors
function handleCacError(error: Error): void {
  const { message } = error;

  if (message.includes('value is missing')) {
    logger.error(
      red(
        `❌ Missing required argument. Please provide a value for the option.`,
      ),
    );
    logger.info(`💡 Use --help to see available options`);
  } else if (message.includes('Unknown option')) {
    logger.error(red(`❌ Unknown option. Please check your command.`));
    logger.info(`💡 Use --help to see available options`);
  } else {
    logger.error(red(`❌ ${message}`));
  }

  process.exit(1);
}

export async function execute<
  T extends GetCommandArgumentsType<typeof analyze>,
>(
  command: Commands.Analyze | `${Commands.Analyze}`,
  options: T['options'],
): Promise<T['result']>;

export async function execute<
  T extends GetCommandArgumentsType<typeof bundleDiff>,
>(
  command: Commands.BundleDiff | `${Commands.BundleDiff}`,
  options: T['options'],
): Promise<T['result']>;

export async function execute(): Promise<void>;
export async function execute(
  command?: `${Commands}` | Commands,
  options?: Common.PlainObject,
): Promise<unknown> {
  const cwd = process.cwd();
  const { name, version } = pkg;

  const ctx: CommandContext = { bin, cwd, name };

  if (command === Commands.Analyze) {
    const { action } = analyze(ctx);

    return action(
      options as GetCommandArgumentsType<typeof analyze>['options'],
    );
  }

  if (command === Commands.StatsAnalyze) {
    const { action } = statsAnalyze(ctx);

    return action(
      options as GetCommandArgumentsType<typeof statsAnalyze>['options'],
    );
  }

  if (command === Commands.BundleDiff) {
    const { action } = bundleDiff(ctx);

    return action(
      options as GetCommandArgumentsType<typeof bundleDiff>['options'],
    );
  }

  const cli = cac(bin);

  cli.version(version);
  cli.help();

  const commands: Command<string>[] = [analyze, bundleDiff, statsAnalyze];

  commands.forEach((cmd) => {
    const { command, description, options, action } = cmd(ctx);

    const commandCli = cli.command(command, description);

    options(commandCli);

    commandCli.action(async (args: CommandArgs) => {
      try {
        // Validate required arguments with proper typing
        validateRequiredArgs(command, args);

        await action(args);
      } catch (error) {
        const { message, stack } = error as Error;
        logger.error(red(stack || message));
        process.exit(1);
      }
    });
  });

  if (process.argv.length <= 2) {
    cli.outputHelp();
    return;
  }

  try {
    cli.parse();
  } catch (error) {
    handleCacError(error as Error);
  }
}

```

### examples/rspress-minimal/rspress.config.ts
```
import * as path from 'node:path';
import { defineConfig } from 'rspress/config';
import { RsdoctorRspackPlugin } from '@rsdoctor/rspack-plugin';

export default defineConfig({
  root: path.join(__dirname, 'docs'),
  title: 'My Site',
  icon: '/rspress-icon.png',
  logo: {
    light: '/rspress-light-logo.png',
    dark: '/rspress-dark-logo.png',
  },
  themeConfig: {
    socialLinks: [
      {
        icon: 'github',
        mode: 'link',
        content: 'https://github.com/web-infra-dev/rspress',
      },
    ],
  },
  builderConfig: {
    tools: {
      rspack(config, { appendPlugins, environment }) {
        if (environment.name === 'node' && process.env.RSDOCTOR) {
          appendPlugins(
            new RsdoctorRspackPlugin({
              output: {
                reportDir: path.join(__dirname, './doc_build/node/'),
              },
            }),
          );
        } else if (process.env.RSDOCTOR) {
          appendPlugins(new RsdoctorRspackPlugin({}));
        }
      },
    },
  },
});

```

### packages/sdk/src/sdk/multiple/controller.ts
```
import { Manifest } from '@rsdoctor/types';
import { RsdoctorPrimarySDK } from './primary';

export class RsdoctorSDKController {
  readonly slaves: RsdoctorPrimarySDK[] = [];

  public root = '';

  constructor(root = process.cwd()) {
    this.root = root;
  }

  get master() {
    return this.slaves[0];
  }

  getLastSdk() {
    return this.slaves[this.slaves.length - 1];
  }

  hasName(name: string) {
    return Boolean(this.slaves.find((item) => item.name === name));
  }

  getSeriesData(serverUrl = false) {
    return this.slaves.map((item) => {
      const data: Manifest.RsdoctorManifestSeriesData = {
        name: item.name,
        path: item.diskManifestPath,
        stage: item.stage,
      };

      if (serverUrl) {
        data.origin = item.server.origin;
      }

      return data;
    });
  }

  createSlave({
    name,
    stage,
    extraConfig,
    type,
  }: Omit<ConstructorParameters<typeof RsdoctorPrimarySDK>[0], 'controller'>) {
    const slave = new RsdoctorPrimarySDK({
      name,
      stage,
      controller: this,
      extraConfig,
      type,
    });
    this.slaves.push(slave);
    // sort by stage after create slave sdk.
    this.slaves.sort((a, b) => a.stage - b.stage);
    return slave;
  }
}

```

### packages/components/src/utils/data/index.ts
```
import { Constants, Manifest } from '@rsdoctor/types';
import { useEffect, useState } from 'react';
import { LocalServerDataLoader } from './local';
import { RemoteDataLoader } from './remote';
import { BaseDataLoader } from './base';
import { getAPILoaderModeFromStorage } from '../storage';
import { APILoaderMode4Dev } from '../../constants';
import { BriefDataLoader } from './brief';

const loaderTask = new WeakMap<
  Manifest.RsdoctorManifestWithShardingFiles,
  Promise<BaseDataLoader>
>();

async function createDataLoader(
  manifest: Manifest.RsdoctorManifestWithShardingFiles,
) {
  try {
    if (process.env.NODE_ENV === 'development') {
      const mode = getAPILoaderModeFromStorage();
      console.log(`[development]-${mode}`);
      if (mode === APILoaderMode4Dev.Local)
        return new LocalServerDataLoader(manifest);
      if (mode === APILoaderMode4Dev.Remote)
        return new RemoteDataLoader(manifest);
    }

    // local server exists
    if (manifest.__LOCAL__SERVER__) {
      console.log(`[LocalServerDataLoader]`);
      return new LocalServerDataLoader(manifest);
    }
  } catch {
    console.log('[DataLoader] fallback to RemoteDataLoader');
  }

  return new RemoteDataLoader(manifest);
}

export function useDataLoader(
  manifest: Manifest.RsdoctorManifestWithShardingFiles | void,
) {
  const [loader, setLoader] = useState<BaseDataLoader | void>(undefined);

  useEffect(() => {
    if (window[Constants.WINDOW_RSDOCTOR_TAG]) {
      console.log('[brief mode]');
      const loader = new BriefDataLoader({ data: [] } as any);
      setLoader(loader);
    }
  }, []);

  useEffect(() => {
    if (!manifest) return;

    if (!loaderTask.has(manifest)) {
      const promise = createDataLoader(manifest);
      loaderTask.set(manifest, promise);
    }

    const task = loaderTask.get(manifest)!;
    task.then((loader) => {
      setLoader(loader);
    });
  }, [manifest]);

  return {
    loader,
  };
}

```

### packages/types/src/manifest.ts
```
import { PlainObject, ObjectPropertyNames } from './common';
import { StoreData } from './sdk';

export interface RsdoctorManifest {
  client: RsdoctorManifestClient;
  /**
   * manifest url in tos, used by inner-rsdoctor.
   */
  cloudManifestUrl?: string;
  /**
   * manifest data shareding file urls in tos, used by inner-rsdoctor.
   */
  cloudData?: Record<keyof RsdoctorManifestData, string[] | string>;
  data: RsdoctorManifestData;
  /** current build name */
  name?: string;
  /**
   * multiple build info
   */
  series?: RsdoctorManifestSeriesData[];
}

export interface RsdoctorManifestSeriesData {
  name: string;
  path: string;
  stage: number;
  origin?: string;
}

export interface RsdoctorManifestWithShardingFiles extends Omit<
  RsdoctorManifest,
  'data'
> {
  data: Record<keyof RsdoctorManifestData, string[] | string>;
  /**
   * manifest data shareding file urls in tos, used by inner-rsdoctor.
   */
  cloudData?: Record<keyof RsdoctorManifestData, string[] | string>;
  /**
   * local server will proxy the manifest content and inject `__LOCAL__SERVER__: true`
   */
  __LOCAL__SERVER__?: boolean;
  __SOCKET__PORT__?: string;
  __SOCKET__URL__?: string;
}

export interface RsdoctorManifestClient {
  enableRoutes: RsdoctorManifestClientRoutes[];
}

// rslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface RsdoctorManifestData extends StoreData {}

export enum RsdoctorManifestClientRoutes {
  Overall = 'Overall',
  Loaders = 'Compile.Loaders',
  ModuleResolve = 'Compile.ModuleResolve',
  Plugins = 'Compile.Plugins',
  BundleSize = 'Bundle.BundleSize',
  ModuleGraph = 'Bundle.ModuleGraph',
  TreeShaking = 'Bundle.TreeShaking',
}

export enum RsdoctorManifestClientConstant {
  WindowPropertyForManifestUrl = '__DEVTOOLS_MANIFEST_URL__',
}

export type RsdoctorManifestObjectKeys = NonNullable<
  ObjectPropertyNames<RsdoctorManifestData>
>;

export type RsdoctorManifestRootKeys = keyof RsdoctorManifestData;

export type RsdoctorManifestMappingKeys =
  | {
      [K in RsdoctorManifestObjectKeys]: RsdoctorManifestData[K] extends PlainObject
        ? RsdoctorManifestData[K] extends Array<unknown>
          ? never
          : string extends keyof RsdoctorManifestData[K]
            ? never
            : keyof RsdoctorManifestData[K] extends string
              ? `${K}.${keyof RsdoctorManifestData[K]}`
              : never
        : never;
    }[RsdoctorManifestObjectKeys]
  | RsdoctorManifestRootKeys;

export type InferManifestDataValue<T> =
  T extends `${infer Scope}.${infer Child}`
    ? Scope extends RsdoctorManifestObjectKeys
      ? Child extends keyof RsdoctorManifestData[Scope]
        ? RsdoctorManifestData[Scope][Child]
        : never
      : never
    : T extends RsdoctorManifestRootKeys
      ? RsdoctorManifestData[T]
      : never;

export interface ManifestDataLoader {
  loadManifest(): Promise<RsdoctorManifest | RsdoctorManifestWithShardingFiles>;
  loadData: {
    <T extends RsdoctorManifestMappingKeys>(
      key: T,
    ): Promise<void | InferManifestDataValue<T>>;
  };
}

```

### packages/client/src/components/BaseApp.tsx
```
import { Constants } from '@rsdoctor/components';
import {
  Config,
  ConfigContext,
  defaultConfig,
} from '@rsdoctor/components/config';
import { Layout } from '@rsdoctor/components/elements';
import {
  getLocale,
  setThemeToStorage,
  setViewModeToStorage,
} from '@rsdoctor/components/utils';
import type { Manifest } from '@rsdoctor/types';
import {
  Button,
  ConfigProvider,
  Divider,
  Result,
  Space,
  Typography,
  theme as te,
} from 'antd';
import React, { useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { HashRouter as BrowserRouter } from 'react-router-dom';

const { PageState, Theme } = Constants;

interface BaseAppProps {
  router: React.ReactNode;
  renderFailState?: () => React.ReactNode;
  extraContent?: React.ReactNode;
}

const BaseApp: React.FC<BaseAppProps> = ({
  router,
  renderFailState,
  extraContent,
}): React.ReactElement => {
  const [state, setState] = useState<Constants.PageState>(PageState.Success);
  const [viewMode, setViewMode] = useState<Config['viewMode']>({
    ...defaultConfig.viewMode,
  });
  const [manifest, setManifest] = useState<Manifest.RsdoctorManifest>();
  const [theme, setTheme] = useState(defaultConfig.theme);

  if (state === Constants.PageState.Fail) {
    if (renderFailState) {
      return <>{renderFailState()}</>;
    }
    return (
      <Space direction="vertical" style={{ padding: 14 }}>
        <Typography.Text strong style={{ fontSize: 16 }}>
          load json file of Rsdoctor failed.
        </Typography.Text>
        <Typography.Text>
          try to use <Typography.Text keyboard>command + r</Typography.Text> to
          refresh page.
        </Typography.Text>
        {process.env.NODE_ENV === 'development' ? (
          <Typography.Text>
            in development, you need to run{' '}
            <Typography.Text keyboard>emo run build:analysis</Typography.Text>{' '}
            to make sure the mock data has been generated.
          </Typography.Text>
        ) : null}
        <Divider />
        <Space direction="vertical" style={{ width: '100%' }}>
          <Typography.Text style={{ fontSize: 16 }}>
            you can
            <Typography.Text strong style={{ fontSize: 'inherit' }}>
              upload a file
            </Typography.Text>
            in the area below to analyze your project.
          </Typography.Text>
          {/* <UploaderComponent /> */}
        </Space>
        <Divider />
      </Space>
    );
  }

  return (
    <BrowserRouter>
      <ConfigContext.Provider
        value={{
          ...defaultConfig,
          theme,
          setTheme: (v) => {
            setTheme(v);
            setThemeToStorage(v);
          },
          pageState: state,
          json: manifest!,
          viewMode,
          setManifest,
          setPageState: setState,
          setViewMode(m, saveStorage = true) {
            const res = { ...viewMode, ...m };
            setViewMode(res);
            if (saveStorage) {
              setViewModeToStorage(res);
            }
          },
        }}
      >
        <ConfigContext.Consumer>
          {(v) => {
            return (
              <ConfigProvider
                locale={getLocale(v.locale)}
                theme={{
                  components: {
                    Layout: {
                      ...(Theme.Light === theme && {
                        headerBg: '#fff',
                      }),
                    },
                  },
                  algorithm:
                    theme === Theme.Dark
                      ? te.darkAlgorithm
                      : te.defaultAlgorithm,

                  token: {
                    padding: 16,
                    fontFamily: 'var(--font-family-code)',
                  },
                }}
              >
                <Layout>
                  <>
                    {extraContent}
                    <ErrorBoundary
                      FallbackComponent={({ error, resetErrorBoundary }) => (
                        <Result
                          status="error"
                          title="Sorry, something went wrong."
                          extra={
                            <Button
                              type="primary"
                              onClick={resetErrorBoundary}
                              loading={state === PageState.Pending}
                            >
                              Reload
                            </Button>
                          }
                        >
                          <Typography.Paragraph>
                            <Typography.Title level={3}>
                              Error Stack
                            </Typography.Title>
                            <pre>{error.stack || error.message}</pre>
                          </Typography.Paragraph>
                        </Result>
                      )}
                      onReset={() => {
                        window.location.reload();
                      }}
                    >
                      {router}
                    </ErrorBoundary>
                  </>
                </Layout>
              </ConfigProvider>
            );
          }}
        </ConfigContext.Consumer>
      </ConfigContext.Provider>
    </BrowserRouter>
  );
};

export default BaseApp;

```

### packages/cli/src/commands/bundle-diff.ts
```
import ora from 'ora';
import { cyan, red } from 'picocolors';
import { Command } from '../types';
import path from 'path';
import fs from 'fs';
import {
  enhanceCommand,
  loadJSON,
  loadShardingFileWithSpinner,
} from '../utils';
import { Commands } from '../constants';
import {
  Client,
  Manifest as ManifestType,
  SDK,
  Constants,
} from '@rsdoctor/types';
import { Manifest, Algorithm, Graph } from '@rsdoctor/utils/common';
import { RsdoctorSDK } from '@rsdoctor/sdk';
import { createRequire } from 'node:module';

interface Options {
  current: string;
  baseline: string;
  open?: boolean;
  html?: boolean;
  json?: boolean | string;
  output?: string;
}

export const bundleDiff: Command<
  Commands.BundleDiff,
  Options,
  RsdoctorSDK<{ name: string; root: string }> | null
> = enhanceCommand(({ cwd, bin, name }) => ({
  command: Commands.BundleDiff,
  description: `
use ${name} to open the bundle diff result in browser for analysis.

example: ${bin} ${Commands.BundleDiff} --baseline="x.json" --current="x.json"
`.trim(),
  options(cli) {
    cli
      .option(
        '--current <path>',
        'the url or file path of the profile json as the current',
      )
      .option(
        '--baseline <path>',
        'the url or file path of the profile json as the baseline',
      )
      .option('--html', 'output as a standalone HTML file')
      .option(
        '--json [path]',
        'output as a JSON file, optionally specify file path (default: rsdoctor-diff.json)',
      )
      .option(
        '--output <path>',
        'output file path for HTML mode (default: rsdoctor-diff.html). For JSON output, use --json [path] to specify the file path.',
      );
  },
  async action({
    baseline,
    current,
    open = true,
    html = false,
    json = false,
    output, // ????
  }) {
    const spinner = ora({ prefixText: cyan(`[${name}]`) }).start();

    spinner.text = `loading "${baseline}"`;
    const baselineData = {
      ...(await loadJSON<ManifestType.RsdoctorManifestWithShardingFiles>(
        baseline,
        cwd,
      )),
      client: {
        enableRoutes: [],
      },
    };

    let baselineDataValue: ManifestType.RsdoctorManifestData;

    try {
      baselineDataValue = await Manifest.fetchShardingFiles(
        baselineData.data,
        (url) => loadShardingFileWithSpinner(url, cwd, spinner),
      );
    } catch (error) {
      if (baselineData.cloudData) {
        spinner.text =
          'load the "baselineData.cloudData" instead of the "baselineData.data"';
        baselineDataValue = await Manifest.fetchShardingFiles(
          baselineData.cloudData,
          (url) => loadShardingFileWithSpinner(url, cwd, spinner),
        );
      } else {
        spinner.fail(red((error as Error).message));
        throw error;
      }
    }

    spinner.text = `loading "${current}"`;
    const currentData = {
      ...(await loadJSON<ManifestType.RsdoctorManifestWithShardingFiles>(
        current,
        cwd,
      )),
      client: {
        enableRoutes: [],
      },
    };

    let currentDataValue: ManifestType.RsdoctorManifestData;

    try {
      currentDataValue = await Manifest.fetchShardingFiles(
        currentData.data,
        (url) => loadShardingFileWithSpinner(url, cwd, spinner),
      );
    } catch (error) {
      if (currentData.cloudData) {
        spinner.text =
          'load the "currentData.cloudData" instead of the "currentData.data"';
        currentDataValue = await Manifest.fetchShardingFiles(
          currentData.cloudData,
          (url) => loadShardingFileWithSpinner(url, cwd, spinner),
        );
      } else {
        spinner.fail(red((error as Error).message));
        throw error;
      }
    }

    if (json && html) {
      spinner.fail(
        red('Options "--json" and "--html" cannot be used together. Please choose one.'),
      );
      return null;
    } else if (json) {
      spinner.text = 'Generating JSON output file...';

      const jsonOutputFile =
        typeof json === 'string' ? json : output || 'rsdoctor-diff.json';
      const outputPath = path.resolve(cwd, jsonOutputFile);
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });

      const jsonData = Graph.getBundleDiffResult(
        baselineDataValue,
        currentDataValue,
      );

      fs.writeFileSync(outputPath, JSON.stringify(jsonData, null, 2), 'utf-8');

      spinner.succeed(`Generated JSON output file at: ${outputPath}`);
      return null;
    }

    // Only start server if not in HTML mode
    if (!html) {
      spinner.text = `start server`;

      const baselineSdk = new RsdoctorSDK({ name, root: cwd });
      const currentSdk = new RsdoctorSDK({ name, root: cwd });

      await Promise.all([baselineSdk.bootstrap(), currentSdk.bootstrap()]);

      const baselineManifestsBuffer = Buffer.from(
        JSON.stringify({
          __LOCAL__SERVER__: true,
          __SOCKET__URL__: baselineSdk.server.socketUrl.socketUrl,
          __SOCKET__PORT__: baselineSdk.server.socketUrl.port,
          ...baselineData,
        }),
      );
      const currentManifestsBuffer = Buffer.from(
        JSON.stringify({
          __LOCAL__SERVER__: true,
          __SOCKET__PORT__: currentSdk.server.socketUrl.port,
          __SOCKET__URL__: currentSdk.server.socketUrl.socketUrl,
          ...currentData,
        }),
      );

      baselineSdk.getStoreData = () => baselineDataValue;
      currentSdk.getStoreData = () => currentDataValue;
      baselineSdk.getManifestData = () => baselineData;
      currentSdk.getManifestData = () => currentData;

      baselineSdk.server.proxy(
        SDK.ServerAPI.API.BundleDiffManifest,
        'GET',
        () => baselineManifestsBuffer,
      );
      currentSdk.server.proxy(
        SDK.ServerAPI.API.BundleDiffManifest,
        'GET',
        () => currentManifestsBuffer,
      );

      spinner.text = `server bootstrap success`;

      const localBaselineManifestUrl =
        baselineSdk.server.origin + SDK.ServerAPI.API.BundleDiffManifest;
      const localCurrentManifestUrl =
        currentSdk.server.origin + SDK.ServerAPI.API.BundleDiffManifest;

      baselineSdk.server.getClientUrl(
        Client.RsdoctorClientRoutes.BundleDiff,
        localBaselineManifestUrl,
        localCurrentManifestUrl,
      );

      if (open) {
        await baselineSdk.server.openClientPage(
          Client.RsdoctorClientRoutes.BundleDiff,
          localBaselineManifestUrl,
          localCurrentManifestUrl,
        );
      }

      return baselineSdk;
    }

    if (html) {
      spinner.text = 'Generating standalone HTML file...';

      const require = createRequire(import.meta.url);
      const clientHtmlPath = require.resolve('@rsdoctor/client/dist/diff.html');
      let htmlContent = fs.readFileSync(clientHtmlPath, 'utf-8');
      const basePath = path.dirname(clientHtmlPath);

      // Extract and inline scripts and styles
      const scriptSrcs = Array.from(
        htmlContent.matchAll(
          /<script[^>]+src=["']([^"']+)["'][^>]*><\/script>/g,
        ),
        (m) => m[1],
      );
      const cssHrefs = Array.from(
        htmlContent.matchAll(/<link\s+href=["'](.+?)["']\s+rel="stylesheet">/g),
        (m) => m[1],
      );

      htmlContent = htmlContent.replace(
        /<script\s+.*?src=["'].*?["']><\/script>/g,
        '',
      );
      htmlContent = htmlContent.replace(
        /<link\s+.*?rel=["']stylesheet["'].*?>/g,
        '',
      );

      // Inline scripts
      const inlinedScripts = scriptSrcs
        .map((src) => {
          const scriptPath = path.resolve(basePath, src);
          try {
            const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
            return `<script>${scriptContent}</script>`;
          } catch (error) {
            console.error(`Could not read script at ${scriptPath}:`, error);
            return '';
          }
        })
        .join('');

      // Inline styles
      const inlinedStyles = cssHrefs
        .map((href) => {
          const cssPath = path.resolve(basePath, href);
          try {
            const cssContent = fs.readFileSync(cssPath, 'utf-8');
            return `<style>${cssContent}</style>`;
          } catch (error) {
            console.error(`Could not read CSS at ${cssPath}:`, error);
            return '';
          }
        })
        .join('');

      // Add inlined resources
      const index = htmlContent.indexOf('</body>');
      htmlContent =
        htmlContent.slice(0, index) +
        inlinedStyles +
        inlinedScripts +
        htmlContent.slice(index);

      // Add compressed data
      const baselineCompressText = Algorithm.compressText(
        JSON.stringify(baselineDataValue),
      );
      const currentCompressText = Algorithm.compressText(
        JSON.stringify(currentDataValue),
      );

      const scripts = [
        // Initialize window object
        `window.${Constants.WINDOW_RSDOCTOR_TAG} = {};`,
        `window.${Constants.WINDOW_RSDOCTOR_TAG}.baseline = ${JSON.stringify(baselineCompressText)};`,
        `window.${Constants.WINDOW_RSDOCTOR_TAG}.current = ${JSON.stringify(currentCompressText)};`,
        `window.${Constants.WINDOW_RSDOCTOR_TAG}.enableRoutes = ${JSON.stringify([Client.RsdoctorClientRoutes.BundleDiff])};`,
        `window.${Constants.WINDOW_RSDOCTOR_TAG}.mode = 'diff';`,
      ];

      const compressTextScripts = scripts
        .map((script) => `<script>${script}</script>`)
        .join('\n');

      htmlContent = htmlContent.replace(
        '<body>',
        `<body>${compressTextScripts}`,
      );

      // Write the output file
      const outputPath = path.resolve(cwd, output || 'rsdoctor-diff.html');
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, htmlContent, 'utf-8');

      spinner.succeed(`Generated standalone HTML file at: ${outputPath}`);
      return null;
    }

    return null;
  },
}));

```

### packages/agent-cli/src/commands/router.ts
```
import { setDataFilePath } from './datasource';
import { createExecutor } from './utils';
import { parseSubcommandOptions } from './utils';

import { findLargeChunks, getChunkById, listChunks } from './handlers/chunks';
import {
  getModuleById,
  getModuleByPath,
  getModuleExports,
  getModuleIssuerPath,
  getSideEffectsHandler as getSideEffects,
} from './handlers/modules';
import {
  detectDuplicatePackages,
  detectSimilarPackages,
  getPackageByName,
  getPackageDependencies,
  listDirectDependencyPackages,
  listPackages,
} from './handlers/packages';
import { diffAssets, getMediaAssets, listAssets } from './handlers/assets';
import { getDirectories, getHotFiles } from './handlers/loaders';
import {
  getConfig,
  getDataFileInfo,
  getSummary,
  listEntrypoints,
  optimizeBundle,
} from './handlers/build';
import {
  getErrorsByCode,
  getErrorsByLevel,
  listErrors,
} from './handlers/errors';
import { listRules } from './handlers/rules';
import {
  getBailoutModules,
  getExportsAnalysis,
  getRetainedModulesHandler,
  getTreeShakingSummary,
} from './handlers/tree-shaking';

interface OptionDef {
  name: string;
  description: string;
  required: boolean;
  type?: 'string' | 'integer' | 'number' | 'boolean';
  default?: unknown;
  enum?: (string | number)[];
  minimum?: number;
  maximum?: number;
}

interface SubcommandDef {
  description: string;
  options: OptionDef[];
  handler: (opts: Record<string, string | true>) => Promise<unknown>;
  toolName?: string;
  toolDescription?: string;
}

interface SourcePaginationConfig {
  page: string;
  pageSize: string;
}

const optimizeStepOptions: OptionDef[] = [
  {
    name: '--step',
    description:
      'Execution step: 1 (basic analysis) or 2 (tree-shaking summary). If not specified, executes both.',
    required: false,
    type: 'integer',
    enum: [1, 2],
  },
];

const pageNumberOption: OptionDef = {
  name: '--page-number',
  description: 'Page number (default: 1)',
  required: false,
  type: 'integer',
  default: 1,
  minimum: 1,
};

const pageSizeOption1000: OptionDef = {
  name: '--page-size',
  description: 'Page size (default: 100, max: 1000)',
  required: false,
  type: 'integer',
  default: 100,
  minimum: 1,
  maximum: 1000,
};

const pageSizeOption100: OptionDef = {
  name: '--page-size',
  description: 'Page size (default: 100, max: 100)',
  required: false,
  type: 'integer',
  default: 100,
  minimum: 1,
  maximum: 100,
};

const pageOptions1000: OptionDef[] = [pageNumberOption, pageSizeOption1000];
const pageOptions100: OptionDef[] = [pageNumberOption, pageSizeOption100];

const sideEffectsCategoryOption: OptionDef = {
  name: '--category',
  description:
    'Filter bailout modules by cause: cjs, barrel, side-effects, or dynamic-import.',
  required: false,
  type: 'string',
  enum: ['cjs', 'barrel', 'side-effects', 'dynamic-import'],
};

function createOptimizeCommand(
  command: Pick<SubcommandDef, 'description' | 'toolName' | 'toolDescription'>,
): SubcommandDef {
  return {
    ...command,
    options: optimizeStepOptions,
    handler: (opts) => optimizeBundle(opts['step'] as string),
  };
}

const SUBCOMMANDS: Record<string, Record<string, SubcommandDef>> = {
  chunks: {
    list: {
      description: 'List all chunks (id, name, size).',
      toolName: 'chunks_list',
      toolDescription:
        'List chunks with ids, names, sizes, and module counts for bundle composition analysis.',
      options: pageOptions1000,
      handler: (opts) =>
        listChunks(opts['page-number'] as string, opts['page-size'] as string),
    },
    'by-id': {
      description: 'Get chunk detail by numeric id.',
      options: [
        {
          name: '--id',
          description: 'Chunk id',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) => getChunkById(opts['id'] as string),
    },
    large: {
      description:
        'Find oversized chunks (>30% over median size and >= 1MB) to prioritize splitChunks suggestions.',
      options: [],
      handler: () => findLargeChunks(),
    },
  },

  modules: {
    'by-id': {
      description: 'Get module detail by id (webpack/rspack).',
      options: [
        {
          name: '--id',
          description: 'Module id',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) => getModuleById(opts['id'] as string),
    },
    'by-path': {
      description:
        'Get module detail by name or path; if multiple match, list them.',
      options: [
        {
          name: '--path',
          description: 'Module name or path',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) => getModuleByPath(opts['path'] as string),
    },
    issuer: {
      description: 'Trace issuer/import chain for a module.',
      options: [
        {
          name: '--id',
          description: 'Module id',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) => getModuleIssuerPath(opts['id'] as string),
    },
    exports: {
      description: 'Get module exports information.',
      options: [],
      handler: () => getModuleExports(),
    },
    'side-effects': {
      description:
        'Get modules with side effects based on bailoutReason, categorized by node_modules and user code.',
      options: [...pageOptions1000, sideEffectsCategoryOption],
      handler: (opts) =>
        getSideEffects(
          opts['page-number'] as string,
          opts['page-size'] as string,
          opts.category as string,
        ),
    },
  },

  packages: {
    list: {
      description: 'List packages with size/duplication info.',
      options: pageOptions1000,
      handler: (opts) =>
        listPackages(
          opts['page-number'] as string,
          opts['page-size'] as string,
        ),
    },
    'by-name': {
      description: 'Get package entries by name.',
      options: [
        {
          name: '--name',
          description: 'Package name',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) => getPackageByName(opts['name'] as string),
    },
    dependencies: {
      description: 'Get package dependency graph.',
      options: pageOptions100,
      handler: (opts) =>
        getPackageDependencies(
          opts['page-number'] as string,
          opts['page-size'] as string,
        ),
    },
    'direct-dependencies': {
      description:
        'List third-party packages directly imported by project/local packages.',
      toolName: 'packages_direct_dependencies',
      toolDescription:
        'List direct third-party package dependencies from project/local packages, excluding transitive third-party-to-third-party dependencies.',
      options: [],
      handler: () => listDirectDependencyPackages(),
    },
    duplicates: {
      description:
        'Detect duplicate packages using E1001 overlay rule if present.',
      toolName: 'packages_duplicates',
      toolDescription:
        'Detect duplicate packages from the current Rsdoctor analysis.',
      options: [],
      handler: () => detectDuplicatePackages(),
    },
    similar: {
      description: 'Detect similar packages (lodash/lodash-es etc.).',
      toolName: 'packages_similar',
      toolDescription:
        'Detect similar package families from the current Rsdoctor analysis.',
      options: [],
      handler: () => detectSimilarPackages(),
    },
  },

  assets: {
    list: {
      description: 'List all assets with size information.',
      options: [],
      handler: () => listAssets(),
    },
    diff: {
      description:
        'Diff asset counts and sizes between two rsdoctor-data.json files (baseline vs current).',
      options: [
        {
          name: '--baseline',
          description: 'Path to baseline rsdoctor-data.json',
          required: true,
          type: 'string',
        },
        {
          name: '--current',
          description: 'Path to current rsdoctor-data.json',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) =>
        diffAssets(opts['baseline'] as string, opts['current'] as string),
    },
    media: {
      description: 'Media asset optimization guidance.',
      options: [],
      handler: () => getMediaAssets(),
    },
  },

  loaders: {
    'hot-files': {
      description:
        'Top third slowest loader/file pairs to surface expensive transforms.',
      options: [
        ...pageOptions1000,
        {
          name: '--min-costs',
          description: 'Minimum costs threshold (ms)',
          required: false,
          type: 'number',
        },
      ],
      handler: (opts) =>
        getHotFiles(
          opts['page-number'] as string,
          opts['page-size'] as string,
          opts['min-costs'] as string,
        ),
    },
    directories: {
      description: 'Loader times grouped by directory.',
      options: [
        ...pageOptions1000,
        {
          name: '--min-total-costs',
          description: 'Minimum total costs threshold (ms)',
          required: false,
          type: 'number',
        },
      ],
      handler: (opts) =>
        getDirectories(
          opts['page-number'] as string,
          opts['page-size'] as string,
          opts['min-total-costs'] as string,
        ),
    },
  },

  build: {
    summary: {
      description: 'Get build summary with costs (build time analysis).',
      toolName: 'build_summary',
      toolDescription:
        'Get build summary with costs and overall build information.',
      options: [],
      handler: () => getSummary(),
    },
    entrypoints: {
      description: 'List all entrypoints in the bundle.',
      options: [],
      handler: () => listEntrypoints(),
    },
    config: {
      description: 'Get build configuration (rspack/webpack config).',
      options: [],
      handler: () => getConfig(),
    },
    optimize: createOptimizeCommand({
      description:
        'Combined bundle optimization inputs: duplicate packages, similar packages, media assets, large chunks, and tree-shaking summary. Supports step-by-step execution.',
    }),
  },

  bundle: {
    optimize: createOptimizeCommand({
      description:
        'Combined bundle optimization inputs (alias for build optimize).',
      toolName: 'bundle_optimize',
      toolDescription:
        'Get bundle optimization inputs including duplicate packages, similar packages, large chunks, and tree-shaking summary signals.',
    }),
  },

  errors: {
    list: {
      description: 'Get all errors and warnings from the build.',
      toolName: 'errors_list',
      toolDescription:
        'Get all build errors and warnings from the current Rsdoctor analysis.',
      options: [],
      handler: () => listErrors(),
    },
    'by-code': {
      description: 'Get errors filtered by error code (e.g., E1001, E1004).',
      options: [
        {
          name: '--code',
          description: 'Error code',
          required: true,
          type: 'string',
        },
      ],
      handler: (opts) => getErrorsByCode(opts['code'] as string),
    },
    'by-level': {
      description: 'Get errors filtered by level (error, warn, info).',
      options: [
        {
          name: '--level',
          description: 'Error level',
          required: true,
          type: 'string',
          enum: ['error', 'warn', 'info'],
        },
      ],
      handler: (opts) => getErrorsByLevel(opts['level'] as string),
    },
  },

  rules: {
    list: {
      description: 'Get rule scan results (overlay alerts).',
      options: [],
      handler: () => listRules(),
    },
  },

  server: {
    port: {
      description: 'Get the JSON data file path used by the CLI.',
      options: [],
      handler: () => getDataFileInfo(),
    },
  },

  'tree-shaking': {
    summary: {
      description:
        'Comprehensive tree-shaking health summary: all rule violation
... [truncated]
```

(+112 more files reference the changed code)
Repository Map
packages/cli/src/commands/analyze.ts
packages/cli/src/commands/bundle-diff.ts
packages/cli/src/commands/index.ts
packages/cli/src/commands/stats-analyze.ts
packages/components/src/utils/data/base.ts
packages/components/src/utils/data/brief.ts
packages/components/src/utils/data/index.ts
packages/components/src/utils/data/local.test.ts
packages/components/src/utils/data/local.ts
packages/components/src/utils/data/remote.ts
packages/components/src/utils/file.tsx
packages/components/src/utils/hooks.ts
packages/components/src/utils/index.ts
packages/components/src/utils/loader.ts
packages/components/src/utils/locale.ts
packages/components/src/utils/manifest.tsx
packages/components/src/utils/request.test.ts
packages/components/src/utils/request.ts
packages/components/src/utils/routes.ts
packages/components/src/utils/size.ts
packages/components/src/utils/socket.test.ts
packages/components/src/utils/socket.ts
packages/components/src/utils/stats.ts
packages/components/src/utils/storage.tsx
packages/components/src/utils/string.ts
packages/components/src/utils/time.ts
packages/components/src/utils/url.ts
packages/core/src/inner-plugins/utils/circleDetect.ts
packages/core/src/inner-plugins/utils/config.ts
packages/core/src/inner-plugins/utils/index.ts
packages/core/src/inner-plugins/utils/loader.ts
packages/core/src/inner-plugins/utils/normalize-config.ts
packages/core/src/inner-plugins/utils/plugin-common.ts
packages/core/src/inner-plugins/utils/plugin.ts
packages/core/src/inner-plugins/utils/sdk.ts
packages/rspack-plugin/src/constants.ts
packages/rspack-plugin/src/index.ts
packages/rspack-plugin/src/multiple.ts
packages/rspack-plugin/src/plugin.ts
packages/sdk/src/sdk/multiple/controller.ts
packages/sdk/src/sdk/multiple/index.ts
packages/sdk/src/sdk/multiple/primary.ts
packages/sdk/src/sdk/multiple/server.ts
packages/sdk/src/sdk/sdk/core.ts
packages/sdk/src/sdk/sdk/index.ts
packages/sdk/src/sdk/sdk/types.ts
packages/sdk/src/sdk/server/fakeServer.ts
packages/sdk/src/sdk/server/index.ts
packages/sdk/src/sdk/server/router.ts
packages/sdk/src/sdk/server/socket/api.ts
packages/sdk/src/sdk/server/socket/index.ts
packages/sdk/src/sdk/server/utils.ts
packages/sdk/tests/module-graph.test.ts
packages/sdk/tests/sdk/core/atomic-write.test.ts
packages/sdk/tests/sdk/core/brief-json-output.test.ts
packages/sdk/tests/sdk/core/hooks.test.ts
packages/sdk/tests/sdk/core/write-pieces-sharding.test.ts
packages/sdk/tests/server/apis/data.test.ts
packages/sdk/tests/server/apis/fs.test.ts
packages/sdk/tests/server/apis/index.test.ts
packages/sdk/tests/server/apis/project.test.ts
packages/sdk/tests/server/apis/renderer.test.ts
packages/sdk/tests/server/utils.test.ts
packages/sdk/tests/server/websocket.test.ts
packages/sdk/tests/utils.ts
packages/types/src/plugin/baseCompiler.ts
packages/types/src/plugin/baseLoader.ts
packages/types/src/plugin/baseStats.ts
packages/types/src/plugin/index.ts
packages/types/src/plugin/internal-rules.ts
packages/types/src/plugin/plugin.ts
packages/types/src/plugin/rspack.ts
packages/types/src/sdk/chunk.ts
packages/types/src/sdk/config.ts
packages/types/src/sdk/context.ts
packages/types/src/sdk/envinfo.ts
packages/types/src/sdk/hooks.ts
packages/types/src/sdk/index.ts
packages/types/src/sdk/instance.ts
packages/types/src/sdk/loader.ts
packages/types/src/sdk/module.ts
packages/types/src/sdk/package.ts
packages/types/src/sdk/plugin.ts
packages/types/src/sdk/process.ts
packages/types/src/sdk/resolver.ts
packages/types/src/sdk/result.ts
packages/types/src/sdk/server/index.ts
packages/types/src/sdk/statement.ts
packages/types/src/sdk/summary.ts
packages/types/src/sdk/treeShaking.ts
packages/utils/src/common/alerts.ts
packages/utils/src/common/algorithm.ts
packages/utils/src/common/bundle.ts
packages/utils/src/common/collection.ts
packages/utils/src/common/crypto.ts
packages/utils/src/common/decycle.ts
packages/utils/src/common/fetch.ts
packages/utils/src/common/file.ts
packages/utils/src/common/global-config.ts
packages/utils/src/common/index.ts
packages/utils/src/common/loader.ts
packages/utils/src/common/lodash.ts
packages/utils/src/common/manifest.ts
packages/utils/src/common/package.ts
packages/utils/src/common/plugin.ts
packages/utils/src/common/resolver.ts
packages/utils/src/common/rspack.ts
packages/utils/src/common/summary.ts
packages/utils/src/common/time.ts
packages/utils/src/common/url.ts
packages/utils/tests/crypto.test.ts
packages/utils/tests/json.test.ts
packages/utils/tests/server.test.ts
./  (3 files)
.agents/skills/  (1 files)
e2e/  (1 files)
e2e/cases/  (13 files)
e2e/test-kit/  (3 files)
examples/rsbuild-minimal/  (9 files)
examples/rspack-banner-minimal/  (11 files)
examples/rspack-layers-minimal/  (13 files)
examples/rspack-minimal/  (12 files)
examples/rspress-minimal/  (1 files)
packages/agent-cli/  (26 files)
packages/ai/  (32 files)
packages/cli/  (7 files)
packages/client/  (10 files)
packages/components/  (153 files)
packages/core/  (65 files)
packages/document/  (15 files)
packages/graph/  (45 files)
packages/rspack-plugin/  (2 files)
packages/sdk/  (21 files)
packages/types/  (38 files)
packages/utils/  (38 files)
scripts/  (4 files)
scripts/test-helper/  (6 files)
... (642 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "rsdoctor-monorepo",
  "private": true,
  "workspaces": {
    "packages": [
      "packages/*"
    ]
  },
  "scripts": {
    "build": "cross-env NX_DAEMON=false nx run-many -t build --projects=@rsdoctor/*,@examples/rsdoctor-rspack-banner --parallel=10",
    "change": "changeset",
    "changeset": "changeset",
    "bump": "changeset version",
    "check-spell": "pnpx cspell && heading-case",
    "check-changeset": "pnpx disallow-major-changeset",
    "check-dependency-version": "pnpx check-dependency-version-consistency . && echo",
    "dev:doc": "cd packages/document && pnpm run dev",
    "e2e": "pnpm run e2e:base && pnpm run e2e:native",
    "e2e:base": "cd ./e2e && pnpm test",
    "e2e:native": "cd ./e2e && cross-env NODE_OPTIONS=--max-old-space-size=8192 pnpm test:native",
    "format": "prettier --experimental-cli --write . && heading-case --write",
    "lint": "rslint",
    "prepare": "pnpm run build && husky",
    "test": "cross-env NODE_OPTIONS=--max-old-space-size=8192 pnpm run ut",
    "test:all": "pnpm run test && pnpm run e2e",
    "sort-package-json": "npx sort-package-json \"packages/*/package.json\"",
    "ut": "rstest run",
    "ut:watch": "rstest"
  },
  "nano-staged": {
    "*.{md,mdx,json,css,less,scss}": "prettier --experimental-cli --write",
    "*.{js,jsx,ts,tsx,mjs,cjs}": [
      "rslint",
      "prettier --experimental-cli --write"
    ],
    "package.json": "pnpm run check-dependency-version"
  },
  "devDependencies": {
    "@rslint/core": "catalog:",
    "@changesets/cli": "^2.31.0",
    "@rsdoctor/tsconfig": "workspace:*",
    "@rslib/core": "0.21.5",
    "@rstest/core": "catalog:",
    "@scripts/test-helper": "workspace:*",
    "cross-env": "catalog:",
    "cspell-ban-words": "^0.0.4",
    "heading-case": "^1.1.3",
    "husky": "^9.1.7",
    "nano-staged": "^0.9.0",
    "nx": "^22.7.5",
    "prettier": "^3.8.4",
    "rsbuild-plugin-publint": "^0.3.4"
  },
  "packageManager": "pnpm@10.33.4",
  "engines": {
    "node": ">=24.15.0",
    "pnpm": ">=10.33.4"
  }
}

```
Context & Existing Test Patterns
Existing test files touched by the patch: packages/cli/src/commands/stats-analyze.test.ts, packages/rspack-plugin/tests/plugin.test.ts, packages/sdk/tests/sdk/core/atomic-write.test.ts, packages/sdk/tests/server/apis/project.test.ts, packages/sdk/tests/server/security.test.ts, packages/sdk/tests/server/socket.test.ts, packages/sdk/tests/utils.ts, packages/utils/tests/server.test.ts
Repository top-level entries: .agents, .changeset, .gitattributes, .github, .gitignore, .husky, .npmrc, .nvmrc, .prettierignore, .prettierrc, .vscode, AGENTS.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, LICENSE, README.md, README.zh-CN.md, SECURITY.md, cspell.config.cjs, e2e, examples, nx.json, package.json, packages, pnpm-lock.yaml, pnpm-workspace.yaml, rslint.config.ts, rstest.config.ts, scripts, skills-lock.json, tsconfig.test.json
Project's own test patterns and conventions:
### e2e/cases/doctor-rspack/uploader.test.ts
```
import { expect, test } from '@playwright/test';
import path from 'path';
import fs from 'fs/promises';
import { getSDK, setSDK } from '@rsdoctor/core/plugins';
import { createRsdoctorPlugin } from './test-utils';

// Dynamic imports to avoid rspack binding issues
let compileByRspack: any;
let Compiler: any;
const originalEnvRSTEST = process.env.RSTEST;
const rspackOutputDir = path.join(__dirname, './dist');
const manifestFileName = 'rsdoctor-data.json';

try {
  const testHelper = require('@scripts/test-helper');
  compileByRspack = testHelper.compileByRspack;
  Compiler = require('@rspack/core').Compiler;
} catch {
  // Skip tests if rspack is not available
  test.skip(true, 'Rspack binding not available, skipping all tests');
}

async function rspackCompile(_tapName: string, compile: any) {
  const file = path.resolve(__dirname, './fixtures/c.js');

  const res = await compile(file, {
    resolve: {
      extensions: ['.ts', '.js'],
    },
    output: {
      path: rspackOutputDir,
    },
    module: {
      rules: [
        {
          test: /\.[jt]s$/,
          use: {
            loader: 'builtin:swc-loader',
            options: {
              jsc: {
                parser: {
                  syntax: 'typescript',
                },
                externalHelpers: true,
                preserveAllComments: false,
              },
            },
          },
          type: 'javascript/auto',
        },
      ],
    },
    plugins: [
      createRsdoctorPlugin({
        disableClientServer: false,
        output: {
          reportDir: rspackOutputDir,
          mode: 'brief',
          options: {
            type: ['json', 'html'],
          },
        },
        port: 8681,
      }),
      {
        name: 'Foo',
        apply(compiler: any) {
          compiler.hooks.beforeRun.tapPromise(
            { name: 'Foo', stage: 99999 },
            async () => {
              const sdk = getSDK();
              if (!sdk) {
                throw new Error('SDK is undefined');
              }
              setSDK(
                new Proxy(sdk as object, {
                  get(target, key, receiver) {
                    switch (key) {
                      case 'reportLoader':
                        return null;
                      case 'reportLoaderStartOrEnd':
                        return (_data: any) => {};
                      default:
                        return Reflect.get(target, key, receiver);
                    }
                  },
                  set(target, key, value, receiver) {
                    return Reflect.set(target, key, value, receiver);
                  },
                  defineProperty(target, p, attrs) {
                    return Reflect.defineProperty(target, p, attrs);
                  },
                }) as any,
              );
            },
          );
        },
      },
    ],
  });

  return res;
}

// Integration test that uses real build artifacts
test.describe('Uploader Integration Tests', () => {
  let manifestPath: string;
  let manifestData: any;

  test.beforeAll(async () => {
    // RSTEST keeps the client server enabled in integration tests.
    process.env.RSTEST = 'true';

    // Skip test if rspack binding is not available
    if (!compileByRspack || !Compiler) {
      test.skip(true, 'Rspack binding not available, skipping test');
      return;
    }
    const tapName = 'Foo';
    await rspackCompile(tapName, compileByRspack);

    manifestPath = path.resolve(rspackOutputDir, manifestFileName);

    await new Promise((resolve) => setTimeout(resolve, 1000));

    try {
      const manifestContent = await fs.readFile(manifestPath, 'utf-8');
      manifestData = JSON.parse(manifestContent);
    } catch (error) {
      throw new Error(
        `Failed to read generated Rsdoctor manifest at ${manifestPath}: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  });

  test('should upload and analyze real build manifest', async ({ page }) => {
    // Skip test if rspack binding is not available
    if (!compileByRspack || !Compiler) {
      test.skip(true, 'Rspack binding not available, skipping test');
      return;
    }
    await page.goto('http://localhost:8681/#/resources/uploader');

    await expect(page.locator('.ant-upload-btn')).toBeVisible();

    // Create file content for upload - use the correct manifest format
    const manifestContent = {
      client: {
        enableRoutes: ['Overall', 'Bundle.ModuleGraph', 'Bundle.BundleSize'],
      },
      data: manifestData.data,
    };
    const fileContent = JSON.stringify(manifestContent);

    // Create a temporary file for upload
    const tempFilePath = path.join(__dirname, 'temp-manifest.json');
    await fs.writeFile(tempFilePath, fileContent);

    try {
      const navigationPromise = page.waitForURL(/.*#\/overall.*/, {
        timeout: 2000,
      });

      // Use Playwright's file upload method
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(tempFilePath);

      await navigationPromise;

      expect(page.url()).toContain('#/overall');

      // Wait for the page to be fully loaded and data to be mounted
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Wait for data to be mounted and verify it's properly loaded
      await page.waitForFunction(
        (tag) => {
          const data = (window as any)[tag];
          return (
            data && data.errors !== undefined && data.moduleGraph !== undefined
          );
        },
        '__RSDOCTOR__',
        { timeout: 10000 },
      );

      // Verify data is properly mounted using browser console execution
      const windowData = await page.evaluate((tag) => {
        return (window as any)[tag];
      }, '__RSDOCTOR__');

      expect(windowData).toBeDefined();

      // Verify the mounted data structure
      if (manifestData.data) {
        expect(windowData).toHaveProperty('errors');
        expect(windowData).toHaveProperty('moduleGraph');
        expect(windowData).toHaveProperty('chunkGraph');
      }

      // Verify enableRoutes are set
      if (manifestData.clientRoutes) {
        expect(windowData.enableRoutes.length).toBeTruthy();
      }
    } finally {
      // Clean up temporary file
      try {
        await fs.unlink(tempFilePath);
      } catch (error) {
        console.warn('Failed to clean up temp file:', error);
      }
    }

    // Test that menus are rendered based on enableRoutes
    if (
      manifestData.clientRoutes &&
      manifestData.clientRoutes.includes('Overall')
    ) {
      // Wait for the page to fully load and render
      await page.waitForTimeout(2000);

      // Try multiple possible selectors for the Bundle Overall menu
      const possibleSelectors = [
        "text='Bundle Overall'",
        "[data-testid='bundle-overall']",
        "text='Overall'",
        ".ant-menu-item:has-text('Bundle Overall')",
        ".ant-menu-item:has-text('Overall')",
      ];

      let found = false;
      for (const selector of possibleSelectors) {
        try {
          const element = page.locator(selector).first();
          await expect(element).toBeVisible({ timeout: 3000 });
          found = true;
          break;
        } catch {
          // Continue to next selector
          console.log(`Selector "${selector}" not found, trying next...`);
        }
      }

      if (!found) {
        // If none of the selectors work, log the page content for debugging
        const pageContent = await page.content();
        console.log('Page content:', pageContent.substring(0, 1000));
        throw new Error(
          'Could not find Bundle Overall menu item with any selector',
        );
      }
    }
  });

  test.afterAll(async () => {
    process.env.RSTEST = originalEnvRSTEST;

    try {
      await fs.rm(rspackOutputDir, {
        recursive: true,
        force: true,
      });
    } catch {
      // Ignore errors
    }
  });
});

```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

