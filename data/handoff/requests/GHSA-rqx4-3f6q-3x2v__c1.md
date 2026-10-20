<!-- label=GHSA-rqx4-3f6q-3x2v call=1 hash=ef5ede8b82 -->
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
- OSV ID: GHSA-rqx4-3f6q-3x2v
- CVE: CVE-2026-59148
- CWE: CWE-306, CWE-352, CWE-732, CWE-942
- Ecosystem / Package: npm / @mockoon/commons-server
- Repository: https://github.com/mockoon/mockoon
- Official Summary: @Mockoon/commons-server: Unauthenticated admin API + wildcard CORS allows mock-state hijack and secret theft

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/packages/app/src/main/libs/server-management.ts b/packages/app/src/main/libs/server-management.ts
index b3bb3c49ea34e336d7b27c719df44b73b33379d9..319db301a79cbf6d49ab498c40f16809e1173267 100644
--- a/packages/app/src/main/libs/server-management.ts
+++ b/packages/app/src/main/libs/server-management.ts
@@ -6,13 +6,48 @@ import {
   Transaction
 } from '@mockoon/commons';
 import { MockoonServer, listenServerEvents } from '@mockoon/commons-server';
+import { randomBytes } from 'node:crypto';
 import { dirname } from 'path';
 import { mainLogger } from 'src/main/libs/logs';
 import { getMainWindow } from 'src/main/libs/main-window';
 import { getSettings } from 'src/main/libs/settings';
 
+const getAdminApiAuthTokenFromEnv = (): string | undefined => {
+  const envValue = process.env['MOCKOON_ADMIN_API_TOKEN'];
+  if (!envValue) {
+    return undefined;
+  }
+
+  // Support CLI-style CSV values in env var, keep first non-empty token.
+  return envValue
+    .split(',')
+    .map((token) => token.trim())
+    .find((token) => token.length > 0);
+};
+
 export class ServerInstance {
   private static instances: Record<string, ServerInstance> = {};
+  private static adminApiAuthTokensByEnvironmentUuid: Record<string, string> =
+    {};
+
+  private static getEnvironmentAdminApiAuthToken = (
+    environmentUuid: string
+  ): string => {
+    const envToken = getAdminApiAuthTokenFromEnv();
+    if (envToken) {
+      return envToken;
+    }
+
+    if (!ServerInstance.adminApiAuthTokensByEnvironmentUuid[environmentUuid]) {
+      ServerInstance.adminApiAuthTokensByEnvironmentUuid[environmentUuid] =
+        randomBytes(32).toString('hex');
+    }
+
+    return ServerInstance.adminApiAuthTokensByEnvironmentUuid[environmentUuid];
+  };
+
+  // Keep one token per environment for the whole desktop app session so
+  // stop/start cycles do not rotate the admin API token for that environment.
   private mockoonServer: MockoonServer | null = null;
 
   constructor(
@@ -76,6 +111,9 @@ export class ServerInstance {
         locale: getSettings().fakerLocale
       },
       envVarsPrefix: getSettings().envVarsPrefix,
+      adminApiAuthToken: ServerInstance.getEnvironmentAdminApiAuthToken(
+        this.environment.uuid
+      ),
       maxTransactionLogs: getSettings().maxLogsPerEnvironment,
       enableRandomLatency: getSettings().enableRandomLatency,
       enableRouteMetadataHeaders: true
@@ -94,7 +132,10 @@ export class ServerInstance {
         mainWindow.webContents.send(
           'APP_SERVER_EVENT',
           this.environment.uuid,
-          'started'
+          'started',
+          {
+            adminApiAuthToken: server.getAdminApiAuthToken()
+          }
         );
       }
     });
diff --git a/packages/app/src/renderer/app/components/dropdown-menu/dropdown-menu.component.html b/packages/app/src/renderer/app/components/dropdown-menu/dropdown-menu.component.html
index 7fbd876713e8a86133a7c3610bdb74e4fd277894..e844145fd18482384107ac85b97a516bdbc2ff16 100644
--- a/packages/app/src/renderer/app/components/dropdown-menu/dropdown-menu.component.html
+++ b/packages/app/src/renderer/app/components/dropdown-menu/dropdown-menu.component.html
@@ -33,7 +33,7 @@
   <div
     class="dropdown-menu"
     [class]="{ 'dropdown-menu-height-content': menuHeightFitContent() }"
-    style="max-width: 40vw"
+    style="max-width: 40vw; max-height: 40vh"
     [id]="idPrefix() + '-dropdown-menu'"
     ngbDropdownMenu
   >
diff --git a/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.html b/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.html
index c080391277dfa5067eeafc6775c990ef299764c7..78d7e52ed3bdb9a513cdc28402bf902520924347 100644
--- a/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.html
+++ b/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.html
@@ -1,6 +1,7 @@
 @let instanceUrl = instanceUrl$ | async;
 @let activeEnvironment = activeEnvironment$ | async;
 @let isActiveEnvironmentEditable = isActiveEnvironmentEditable$ | async;
+@let activeEnvironmentStatus = activeEnvironmentStatus$ | async;
 
 @if (activeEnvironment) {
   <div class="d-flex flex-column h-100 p-2" [formGroup]="activeEnvironmentForm">
@@ -78,6 +79,71 @@
       }
     </div>
 
+    @if (!isWeb) {
+      <app-title-separator heading="Admin API" icon="endpoints">
+        <div subheading>
+          Admin API available on
+          {{
+            instanceUrl +
+              (activeEnvironment.endpointPrefix
+                ? '/' + activeEnvironment.endpointPrefix
+                : '')
+          }}/mockoon-admin
+        </div>
+      </app-title-separator>
+
+      <div class="input-group align-items-center mb-3">
+        <span class="text-muted">
+          Each mock exposes an admin API for runtime state and logs
+          <a
+            class="text-primary ms-1"
+            [href]="adminApiDocsUrl"
+            target="_blank"
+            rel="noopener noreferrer"
+            ngbTooltip="Open admin API documentation"
+            aria-label="Open admin API documentation"
+          >
+            <app-svg icon="info" /> </a
+          >. You can use the token below to authenticate your requests to the
+          admin API.
+        </span>
+      </div>
+
+      <div class="input-group align-items-center">
+        <label for="env-settings-admin-api-token" class="pe-2"
+          >Admin API token</label
+        >
+        <div class="col-4">
+          <input
+            type="text"
+            class="form-control"
+            id="env-settings-admin-api-token"
+            [value]="
+              activeEnvironmentStatus?.running &&
+              activeEnvironmentStatus?.adminApiAuthToken
+                ? activeEnvironmentStatus?.adminApiAuthToken
+                : 'Start the environment to generate a token'
+            "
+            readonly
+          />
+        </div>
+        <button
+          type="button"
+          class="btn btn-link"
+          ngbTooltip="Copy token to clipboard"
+          [disabled]="
+            !activeEnvironmentStatus?.running ||
+            !activeEnvironmentStatus?.adminApiAuthToken
+          "
+          (click)="
+            copyAdminApiToken(activeEnvironmentStatus!.adminApiAuthToken!)
+          "
+        >
+          <app-svg icon="assignment" />
+        </button>
+      </div>
+    }
+
     @if (!isWeb) {
       <app-title-separator
         heading="TLS"
diff --git a/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts b/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts
index 1e7b687d85d39864a7e48f6ddf211a1a6f3c0d1e..a50ccea57955569155913e2dddc4591d78f67b87 100644
--- a/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts
+++ b/packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts
@@ -18,6 +18,7 @@ import { InputNumberDirective } from 'src/renderer/app/directives/input-number.d
 import { ValidPathDirective } from 'src/renderer/app/directives/valid-path.directive';
 import { buildApiUrl } from 'src/renderer/app/libs/utils.lib';
 import { ToggleItems } from 'src/renderer/app/models/common.model';
+import { EnvironmentStatus } from 'src/renderer/app/models/store.model';
 import { DialogsService } from 'src/renderer/app/services/dialogs.service';
 import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
 import { Store } from 'src/renderer/app/stores/store';
@@ -46,8 +47,10 @@ export class EnvironmentSettingsComponent {
   private dialogsService = inject(DialogsService);
   public activeEnvironment$: Observable<Environment>;
   public instanceUrl$: Observable<string>;
+  public activeEnvironmentStatus$: Observable<EnvironmentStatus>;
   public activeEnvironmentForm: UntypedFormGroup;
   public Infinity = Infinity;
+  public adminApiDocsUrl = Config.docs.adminApi;
   public certTypes: ToggleItems = [
     {
       value: 'CERT',
@@ -89,6 +92,8 @@ export class EnvironmentSettingsComponent {
       })
     );
 
+    this.activeEnvironmentStatus$ = this.store.selectActiveEnvironmentStatus();
+
     this.activeEnvironmentForm = this.formBuilder.group({
       name: [EnvironmentDefault.name],
       hostname: [EnvironmentDefault.hostname],
@@ -166,4 +171,8 @@ export class EnvironmentSettingsComponent {
       )
       .subscribe();
   }
+
+  public copyAdminApiToken(token: string) {
+    navigator.clipboard.writeText(token);
+  }
 }
diff --git a/packages/app/src/renderer/app/models/main-api.model.ts b/packages/app/src/renderer/app/models/main-api.model.ts
index 1b1e7b6bf7b409cc96154f3157606c1b0b58f7e0..3a0433ca839e761ed4b0f5c2c4b96c130a00ee4a 100644
--- a/packages/app/src/renderer/app/models/main-api.model.ts
+++ b/packages/app/src/renderer/app/models/main-api.model.ts
@@ -117,6 +117,7 @@ export interface MainAPIModel {
         transaction?: Transaction;
         inflightRequest?: InFlightRequest;
         dataBuckets?: ProcessedDatabucketWithoutValue[];
+        adminApiAuthToken?: string;
       }
     ) => void
   ): void;
diff --git a/packages/app/src/renderer/app/models/store.model.ts b/packages/app/src/renderer/app/models/store.model.ts
index 829968f2fedba1bf7a718878ff8cc6b96c760472..c1e9bf9ea482cf468800f9f6522b64f6f8d8b5eb 100644
--- a/packages/app/src/renderer/app/models/store.model.ts
+++ b/packages/app/src/renderer/app/models/store.model.ts
@@ -53,6 +53,7 @@ export type EnvironmentStatus = {
   running: boolean;
   needRestart: boolean;
   redeploying: boolean;
+  adminApiAuthToken?: string | null;
 };
 
 export type EnvironmentsStatuses = Record<string, EnvironmentStatus>;
diff --git a/packages/app/src/renderer/app/services/server.service.ts b/packages/app/src/renderer/app/services/server.service.ts
index 1ab7fd7a7cffc1b56a8ceb98f03e976311f3d17b..bff7f2486cfb03426432d560453d799e64fdf722 100644
--- a/packages/app/src/renderer/app/services/server.service.ts
+++ b/packages/app/src/renderer/app/services/server.service.ts
@@ -304,7 +304,11 @@ export class ServerService {
         this.zone.run(() => {
           this.store.update(
             updateEnvironmentStatusAction(
-              { running: true, needRestart: false },
+              {
+                running: true,
+                needRestart: false,
+                adminApiAuthToken: data?.adminApiAuthToken || null
+              },
               environment.uuid
             )
           );
@@ -317,7 +321,8 @@ export class ServerService {
             updateEnvironmentStatusAction(
               {
                 running: false,
-                needRestart: false
+                needRestart: false,
+                adminApiAuthToken: null
               },
               environment.uuid
             )
diff --git a/packages/app/src/shared/shared-config.ts b/packages/app/src/shared/shared-config.ts
index 74897cb398a0db8b1e3222cd19f66dcaf54e9666..2a5a3c93e32e4a73cf227496e3dc12d96a51761c 100644
--- a/packages/app/src/shared/shared-config.ts
+++ b/packages/app/src/shared/shared-config.ts
@@ -30,6 +30,7 @@ export const SharedConfig = (options: {
     changelogMarkdownURL: `${options.websiteURL}desktop-changelogs-markdown/`,
     releasePublicURL: `${options.websiteURL}releases/`,
     docs: {
+      adminApi: `${docsUrl}admin-api/overview/`,
       templating: `${docsUrl}templating/overview/`,
       proxy: `${docsUrl}server-configuration/proxy-mode/`,
       cors: `${docsUrl}server-configuration/cors/`,
diff --git a/packages/cli/src/commands/start.ts b/packages/cli/src/commands/start.ts
index 9a8987e8e3ce89f4e18e3fdaf4526a2b7d5c7d2d..c86adef9bff086c2e04966559c0bbbddb8816f7a 100644
--- a/packages/cli/src/commands/start.ts
+++ b/packages/cli/src/commands/start.ts
@@ -100,6 +100,18 @@ export default class Start extends Command {
         'Disable the admin API, enabled by default (more info: https://mockoon.com/docs/latest/admin-api/overview/)',
       default: false
     }),
+    'admin-api-token': Flags.string({
+      description:
+        'Admin API bearer token(s). Provide once to reuse for all environments, or multiple times (or comma-separated) to set one token per environment.',
+      multiple: true,
+      env: 'MOCKOON_ADMIN_API_TOKEN'
+    }),
+    'admin-api-cors-origin': Flags.string({
+      description:
+        "Allowed CORS origin(s) for the admin API (e.g. 'https://app.example.com'). Provide multiple times or comma-separated for multiple origins. Use '*' to explicitly opt into wildcard CORS. When omitted, no CORS headers are emitted on admin API responses.",
+      multiple: true,
+      env: 'MOCKOON_ADMIN_API_CORS_ORIGIN'
+    }),
     'disable-tls': Flags.boolean({
       description:
         'Disable TLS for all environments. TLS configuration is part of the environment configuration (more info: https://mockoon.com/docs/latest/server-configuration/serving-over-tls/).',
@@ -146,6 +158,13 @@ export default class Start extends Command {
 
   public async run(): Promise<void> {
     const { flags: userFlags } = await this.parse(Start);
+    const adminApiTokens = this.resolveTokens(
+      userFlags['admin-api-token'],
+      userFlags.data.length
+    );
+    const adminApiCorsOrigins = this.normalizeCsvFlag(
+      userFlags['admin-api-cors-origin']
+    );
 
     // validate flags
     if (
@@ -203,6 +222,9 @@ export default class Start extends Command {
           },
           envVarsPrefix: userFlags['env-vars-prefix'],
           enableAdminApi: !userFlags['disable-admin-api'],
+          adminApiAuthToken: adminApiTokens[index],
+          adminApiCorsOrigins:
+            adminApiCorsOrigins.length > 0 ? adminApiCorsOrigins : undefined,
           disableTls: userFlags['disable-tls'],
           maxTransactionLogs: userFlags['max-transaction-logs'],
           enableRandomLatency: userFlags['enable-random-latency'],
@@ -269,6 +291,8 @@ export default class Start extends Command {
       fakerOptions: parameters.fakerOptions,
       envVarsPrefix: parameters.envVarsPrefix,
       enableAdminApi: parameters.enableAdminApi,
+      adminApiAuthToken: parameters.adminApiAuthToken,
+      adminApiCorsOrigins: parameters.adminApiCorsOrigins,
       disableTls: parameters.disableTls,
       maxTransactionLogs: parameters.maxTransactionLogs,
       enableRandomLatency: parameters.enableRandomLatency,
@@ -338,4 +362,44 @@ export default class Start extends Command {
 
     return server;
   };
+
+  private resolveTokens = (
+    rawTokens: string[] | string | undefined,
+    environmentsCount: number
+  ): (string | undefined)[] => {
+    const parsedTokens = this.normalizeCsvFlag(rawTokens);
+
+    if (parsedTokens.length === 0) {
+      return Array.from({ length: environmentsCount }, () => undefined);
+    }
+
+    if (parsedTokens.length === 1) {
+      return Array.from({ length: environmentsCount }, () => parsedTokens[0]);
+    }
+
+    if (parsedTokens.length !== environmentsCount) {
+      this.error(
+        `The number of provided API tokens (${parsedTokens.length}) must be 1 or match the number of environments (${environmentsCount}).`
+      );
+    }
+
+    return parsedTokens;
+  };
+
+  /**
+   * Normalize an oclif flag value that may arrive as a single CSV string
+   * (when set through an env var) or an array (when set through repeated
+   * CLI flags), into a flat array of trimmed, non-empty values.
+   */
+  private normalizeCsvFlag = (
+    rawValue: string[] | string | undefined
+  ): string[] => {
+    const values =
+      rawValue == null ? [] : Array.isArray(rawValue) ? rawValue : [rawValue];
+
+    return values
+      .flatMap((value) => value.split(','))
+      .map((value) => value.trim())
+      .filter((value) => value.length > 0);
+  };
 }
diff --git a/packages/commons-server/src/constants/server-messages.constants.ts b/packages/commons-server/src/constants/server-messages.constants.ts
index c07e69b637ce35e616d7dc89e4d55f58a65d85ce..7d82da96d54c613553f284d545e4d4d0e131ba4e 100644
--- a/packages/commons-server/src/constants/server-messages.constants.ts
+++ b/packages/commons-server/src/constants/server-messages.constants.ts
@@ -16,6 +16,7 @@ export const ServerMessages = {
   HEADER_PARSING_ERROR_LIGHT:
     '-- Header parsing error, see logs for more details --',
   SERVER_STARTED: 'Server started on port %d',
+  ADMIN_API_AUTH_AUTO_GENERATED_TOKEN: 'Admin API token (auto-generated): %s',
   SERVER_STOPPED: 'Server stopped',
   CALLBACK_FILE_ERROR: 'Error while attaching file to callback request: %s',
   CALLBACK_ERROR: 'Error while executing callback: %s',
diff --git a/packages/commons-server/src/libs/logger.ts b/packages/commons-server/src/libs/logger.ts
index 1b4d04525a05dec6ad30dd316ce5687989422a90..94bd4426c025db2622997427ffb42d4a4a85b559 100644
--- a/packages/commons-server/src/libs/logger.ts
+++ b/packages/commons-server/src/libs/logger.ts
@@ -10,26 +10,53 @@ import {
   FileTransportOptions
 } from 'winston/lib/winston/transports';
 
+const autoGeneratedTokenMessagePatterns = [
+  /(Admin API token \(auto-generated\):\s*)(.+)$/i
+];
+
+const redactAutoGeneratedTokenMessage = (value: string): string =>
+  autoGeneratedTokenMessagePatterns.reduce(
+    (redactedValue, pattern) => redactedValue.replace(pattern, '$1[REDACTED]'),
+    value
+  );
+
+const fileTransportRedactionFormat = logFormat((info) => {
+  if (typeof info.message === 'string') {
+    info.message = redactAutoGeneratedTokenMessage(info.message);
+  }
+
+  return info;
+});
+
 export const createLoggerInstance = (
   fileTransportOptions?: FileTransportOptions | null
 ): Logger => {
   const transportsInstances: (
     | FileTransportInstance
     | ConsoleTransportInstance
-  )[] = [new logsTransports.Console({ handleExceptions: true })];
+  )[] = [
+    new logsTransports.Console({
+      handleExceptions: true,
+      format: logFormat.combine(logFormat.timestamp(), logFormat.json())
+    })
+  ];
 
   if (fileTransportOptions) {
     transportsInstances.push(
       new logsTransports.File({
         ...fileTransportOptions,
-        handleExceptions: true
+        handleExceptions: true,
+        format: logFormat.combine(
+          fileTransportRedactionFormat(),
+          logFormat.timestamp(),
+          logFormat.json()
+        )
       })
     );
   }
 
   return createLogger({
     level: 'info',
-    format: logFormat.combine(logFormat.timestamp(), logFormat.json()),
     transports: transportsInstances,
     exitOnError: false
   });
diff --git a/packages/commons-server/src/libs/server/admin-api.ts b/packages/commons-server/src/libs/server/admin-api.ts
index 95be214cde37da8367aa4ac2e49ccf7b42bb64b0..91bd542829e4259e5a53a07872a244b138ddd89a 100644
--- a/packages/commons-server/src/libs/server/admin-api.ts
+++ b/packages/commons-server/src/libs/server/admin-api.ts
@@ -1,5 +1,12 @@
-import { Environment, EnvironmentSchema, Transaction } from '@mockoon/commons';
+import {
+  Environment,
+  EnvironmentSchema,
+  extractBearerToken,
+  Transaction
+} from '@mockoon/commons';
 import { Express, Request, Response } from 'express';
+import { timingSafeEqual } from 'node:crypto';
+import { redactTransaction } from '../utils';
 import { MockoonServer } from './server';
 import { Sse } from './sse';
 
@@ -21,6 +28,8 @@ export const createAdminEndpoint = (
     getLogs,
     purgeLogs,
     envVarsPrefix,
+    adminApiAuthToken,
+    adminApiCorsOrigins,
     updateEnvironment
   }: {
     statePurgeCallback: () => void;
@@ -33,6 +42,8 @@ export const createAdminEndpoint = (
     getLogs: () => Transaction[];
     purgeLogs: () => void;
     envVarsPrefix: string;
+    adminApiAuthToken: string;
+    adminApiCorsOrigins?: string[];
     updateEnvironment: (environment: Environment) => void;
   }
 ): void => {
@@ -54,22 +65,86 @@ export const createAdminEndpoint = (
         ...replayableEvents,
         ...limitedLogs.map((transaction) => ({
           event: 'transaction-complete',
-          transaction
+          transaction: redactTransaction(transaction)
         }))
       ];
     }
   });
 
   app.use(`${adminApiPrefix}*`, (req, res, next) => {
-    res.setHeaders(
-      new Headers({
-        'Access-Control-Allow-Origin': '*',
-        'Access-Control-Allow-Methods':
-          'GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS',
-        'Access-Control-Allow-Headers':
-          'Content-Type, Origin, Accept, Authorization, Content-Length, X-Requested-With'
-      })
-    );
+    const allowedOrigins = adminApiCorsOrigins ?? [];
+    const allowAll = allowedOrigins.includes('*');
+    const requestOrigin = req.get('origin');
+    const matchedOrigin = allowAll
+      ? '*'
+      : requestOrigin && allowedOrigins.includes(requestOrigin)
+        ? requestOrigin
+        : undefined;
+
+    if (matchedOrigin) {
+      res.setHeader('Access-Control-Allow-Origin', matchedOrigin);
+      if (matchedOrigin !== '*') {
+        res.setHeader('Vary', 'Origin');
+      }
+      res.setHeader(
+        'Access-Control-Allow-Methods',
+        'GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS'
+      );
+      res.setHeader(
+        'Access-Control-Allow-Headers',
+        'Content-Type, Origin, Accept, Authorization, Content-Length, X-Requested-With'
+      );
+    }
+
+    if (req.method === 'OPTIONS') {
+      // Always terminate preflight at the admin endpoint to avoid leaking
+      // to user-defined routes. Browsers will reject the response if no
+      // matching Access-Control-Allow-Origin header is present.
+      res.status(matchedOrigin ? 204 : 403).end();
+
+      return;
+    }
+
+    next();
+  });
+
+  const adminApiUnauthorized = (res: Response) => {
+    res.status(401).send({ message: 'Unauthorized' });
+  };
+
+  const hasValidAdminApiToken = (providedToken: string): boolean => {
+    const expectedTokenBuffer = Buffer.from(adminApiAuthToken, 'utf8');
+    const providedTokenBuffer = Buffer.from(providedToken, 'utf8');
+
+    if (expectedTokenBuffer.length !== providedTokenBuffer.length) {
+      return false;
+    }
+
+    return timingSafeEqual(expectedTokenBuffer, providedTokenBuffer);
+  };
+
+  app.use(`${adminApiPrefix}*`, (req: Request, res: Response, next) => {
+    if (req.method === 'OPTIONS') {
+      next();
+
+      return;
+    }
+
+    const isSseEndpoint =
+      req.method === 'GET' && req.baseUrl === `${adminApiPrefix}/events`;
+    const bearerToken = extractBearerToken(req.get('authorization'));
+    const sseQueryToken =
+      isSseEndpoint && typeof req.query['token'] === 'string'
+        ? req.query['token'].trim()
+        : undefined;
+    const providedToken = bearerToken || sseQueryToken;
+
+    if (!providedToken || !hasValidAdminApiToken(providedToken)) {
+      adminApiUnauthorized(res);
+
+      return;
+    }
+
     next();
   });
 
@@ -86,7 +161,10 @@ export const createAdminEndpoint = (
 
   // listen to server events and send them through the SSE
   serverInstance.on('transaction-complete', (transaction) => {
-    const event = { event: 'transaction-complete', transaction };
+    const event = {
+      event: 'transaction-complete',
+      transaction: redactTransaction(transaction)
+    };
 
     events.send(event);
   });
@@ -143,7 +221,15 @@ export const createAdminEndpoint = (
   };
 
   /**
-   * Set the value of an environment variable
+   * Set the value of an environment variable.
+   *
+   * The key must start with the configured prefix to prevent arbitrary
+   * environment variable writes (e.g. PATH, NODE_OPTIONS). If the key
+   * does not start with the prefix, it is automatically prepended,
+   * mirroring the read handler behavior.
+   *
+   * When the prefix is empty, writes are rejected to avoid arbitrary
+   * environment variable writes.
    *
    * @param req
    * @param res
@@ -151,15 +237,28 @@ export const createAdminEndpoint = (
   const setEnvVarHandler = (req, res) => {
     try {
       const { key, value } = req.body;
-      if (key !== undefined && value !== undefined) {
-        process.env[key] = value;
+      if (key === undefined || value === undefined) {
+        throw new Error('Key or value missing from request');
+      }
 
-        res.send({
-          message: `Environment variable '${key}' has been set to '${value}'`
+      if (!envVarsPrefix) {
+        res.status(403).send({
+          message:
+            'Environment variable writes are disabled when the prefix is empty'
         });
-      } else {
-        throw new Error('Key or value missing from request');
+
+        return;
       }
+
+      const prefixedKey = key.startsWith(envVarsPrefix)
+        ? key
+        : envVarsPrefix + key;
+
+      process.env[prefixedKey] = value;
+
+      res.send({
+        message: `Environment variable '${prefixedKey}' has been set to '${value}'`
+      });
     } catch (_error) {
       res.status(400).send({ message: 'Invalid request' });
     }
@@ -306,7 +405,7 @@ export const createAdminEndpoint = (
     const logs = getLogs();
     const start = (page - 1) * limit;
 
-    res.send(logs.slice(start, start + limit));
+    res.send(logs.slice(start, start + limit).map(redactTransaction));
   };
 
   /**
diff --git a/packages/commons-server/src/libs/server/events-listeners.ts b/packages/commons-server/src/libs/server/events-listeners.ts
index 224a17b8602f8c9a9a79e34772cfceb8d288ee9e..c8a568ee587ab0a47942fcbda6f6c69443227ad3 100644
--- a/packages/commons-server/src/libs/server/events-listeners.ts
+++ b/packages/commons-server/src/libs/server/events-listeners.ts
@@ -1,7 +1,6 @@
 import {
   CloneObject,
   Environment,
-  Header,
   InFlightRequest,
   InvokedCallback,
   Methods,
@@ -10,19 +9,9 @@ import {
 import { format } from 'util';
 import { Logger } from 'winston';
 import { ServerMessages } from '../../constants/server-messages.constants';
+import { redactHeaders, redactInFlightRequestInPlace } from '../utils';
 import { MockoonServer } from './server';
 
-const authorizationHeaders = ['authorization', 'proxy-authorization'];
-const filterAuthorizationHeaders = (header: Header) => {
-  if (authorizationHeaders.includes(header.key.toLowerCase())) {
-    const headerSplit = header.value.split(' ');
-
-    header.value = headerSplit.length === 1 ? '***' : `${headerSplit[0]} ***`;
-  }
-
-  return header;
-};
-
 export const listenServerEvents = function (
   server: MockoonServer,
   environment: Environment,
@@ -40,6 +29,21 @@ export const listenServerEvents = function (
       ...defaultLogMeta
     });
 
+    if (
+      server.isAdminApiEnabled() &&
+      server.isAdminApiAuthTokenAutoGenerated()
+    ) {
+      logger.warn(
+        format(
+          ServerMessages.ADMIN_API_AUTH_AUTO_GENERATED_TOKEN,
+          server.getAdminApiAuthToken()
+        ),
+        {
+          ...defaultLogMeta
+        }
+      );
+    }
+
     if (process.send) {
       process.send('ready');
     }
@@ -108,10 +112,12 @@ export const listenServerEvents = function (
 
     if (logTransaction) {
       logMeta.transaction = CloneObject(transaction) as Transaction;
-      logMeta.transaction.request.headers =
-        logMeta.transaction.request.headers.map(filterAuthorizationHeaders);
-      logMeta.transaction.response.headers =
-        logMeta.transaction.response.headers.map(filterAuthorizationHeaders);
+      logMeta.transaction.request.headers = redactHeaders(
+        logMeta.transaction.request.headers
+      );
+      logMeta.transaction.response.headers = redactHeaders(
+        logMeta.transaction.response.headers
+      );
       logMeta.transaction.request.method =
         logMeta.transaction.request.method.toUpperCase() as Methods;
     }
@@ -131,11 +137,11 @@ export const listenServerEvents = function (
     if (logTransaction) {
       const clonedCallback = CloneObject(callback) as InvokedCallback;
       logMeta.callback = clonedCallback;
-      logMeta.callback.requestHeaders = logMeta.callback.requestHeaders.map(
-        filterAuthorizationHeaders
+      logMeta.callback.requestHeaders = redactHeaders(
+        logMeta.callback.requestHeaders
       );
-      logMeta.callback.responseHeaders = logMeta.callback.responseHeaders.map(
-        filterAuthorizationHeaders
+      logMeta.callback.responseHeaders = redactHeaders(
+        logMeta.callback.responseHeaders
       );
     }
     logger.info('Callback invoked', logMeta);
@@ -150,13 +156,9 @@ export const listenServerEvents = function (
     };
 
     if (logTransaction) {
-      logMeta.inflightRequest = CloneObject(inflightRequest) as InFlightRequest;
-      logMeta.inflightRequest.request.headers = logMeta.inflightRequest.request
-        ?.headers
-        ? logMeta.inflightRequest.request?.headers.map(
-            filterAuthorizationHeaders
-          )
-        : [];
+      logMeta.inflightRequest = redactInFlightRequestInPlace(
+        CloneObject(inflightRequest) as InFlightRequest
+      );
     }
     logger.info('New WebSocket connection', logMeta);
   });
@@ -173,16 +175,10 @@ export const listenServerEvents = function (
         };
 
       if (logTransaction) {
-        logMeta.inflightRequest = CloneObject(
-          inflightRequest
-        ) as InFlightRequest;
+        logMeta.inflightRequest = redactInFlightRequestInPlace(
+          CloneObject(inflightRequest) as InFlightRequest
+        );
         logMeta.messageData = message;
-        logMeta.inflightRequest.request.headers = logMeta.inflightRequest
-          .request?.headers
-          ? logMeta.inflightRequest.request?.headers.map(
-              filterAuthorizationHeaders
-            )
-          : [];
       }
       logger.info('WebSocket message received', logMeta);
     }
@@ -199,13 +195,9 @@ export const listenServerEvents = function (
       };
 
       if (logTransaction) {
-        logMeta.inflightRequest = CloneObject(request) as InFlightRequest;
-        logMeta.inflightRequest.request.headers = logMeta.inflightRequest
-          .request?.headers
-          ? logMeta.inflightRequest.request?.headers.map(
-              filterAuthorizationHeaders
-            )
-          : [];
+        logMeta.inflightRequest = redactInFlightRequestInPlace(
+          CloneObject(request) as InFlightRequest
+        );
       }
 
       logger.info('WebSocket closed', logMeta);
diff --git a/packages/commons-server/src/libs/server/server.ts b/packages/commons-server/src/libs/server/server.ts
index 3a7b354dcc01a49e2a72563f31f35589878e867e..50f45106b61d53caf5661987137a995ac83ca56f 100644
--- a/packages/commons-server/src/libs/server/server.ts
+++ b/packages/commons-server/src/libs/server/server.ts
@@ -27,6 +27,7 @@ import {
   defaultMaxCallbackDepth,
   defaultMaxTransactionLogs,
   deterministicStringify,
+  generateSecureToken,
   generateUUID,
   getLatency,
   pathMatch,
@@ -112,6 +113,8 @@ import {
  * ```
  */
 export class MockoonServer extends (EventEmitter as new () => TypedEmitter<ServerEvents>) {
+  private adminApiAuthToken: string;
+  private adminApiAuthTokenIsAutoGenerated = false;
   private serverInstance: httpServer | httpsServer;
   private webSocketServers: WebSocketServerInstance[] = [];
   private tlsOptions: SecureContextOptions = {};
@@ -150,6 +153,13 @@ export class MockoonServer extends (EventEmitter as new () => TypedEmitter<Serve
       maxCallbackDepth: options.maxCallbackDepth ?? defaultMaxCallbackDepth
     };
 
+    if (this.options.adminApiAuthToken) {
+      this.adminApiAuthToken = this.options.adminApiAuthToken;
+    } else {
+      this.adminApiAuthToken = generateSecureToken(32);
+      this.adminApiAuthTokenIsAutoGenerated = true;
+    }
+
     this.computeEffectiveRestRoutes();
     this.computeEffectiveWebSocketRoutes();
   }
@@ -237,6 +247,18 @@ export class MockoonServer extends (EventEmitter as new () => TypedEmitter<Serve
     }
   }
 
+  public getAdminApiAuthToken(): string {
+    return this.adminApiAuthToken;
+  }
+
+  public isAdminApiEnabled(): boolean {
+    return this.options.enableAdminApi;
+  }
+
+  public isAdminApiAuthTokenAutoGenerated(): boolean {
+    return this.adminApiAuthTokenIsAutoGenerated;
+  }
+
   /**
    * Create a request listener
    */
@@ -293,6 +315,8 @@ export class MockoonServer extends (EventEmitter as new () => TypedEmitter<Serve
           this.transactionLogs = [];
         },
         envVarsPrefix: this.options.envVarsPrefix,
+        adminApiAuthToken: this.adminApiAuthToken,
+        adminApiCorsOrigins: this.options.adminApiCorsOrigins,
         updateEnvironment: (environment: Environment) => {
           this.updateEnvironment(environment);
         }
diff --git a/packages/commons-server/src/libs/utils.ts b/packages/commons-server/src/libs/utils.ts
index 13ff2cc5ade0b959128c7488b56ca4555e7f56c0..a98097071cdc8e184ed871f8d139db0e7a01c3a7 100644
--- a/packages/commons-server/src/libs/utils.ts
+++ b/packages/commons-server/src/libs/utils.ts
@@ -30,6 +30,96 @@ import { ServerRequest } from './requests';
 export { lookup as mimeTypeLookup } from 'mime-types';
 export { get as objectGetPath } from 'object-path';
 
+/**
+ * Header names whose values are redacted before transactions are exposed
+ * outside of the original process trust boundary.
+ *
+ * Applied to:
+ *  - Admin API output (SSE stream + GET /logs)
+ *  - CLI / serverless transaction logs (--log-transaction)
+ *
+ * NOT applied to:
+ *  - Desktop "Logs" tab (transactions reach the renderer through local IPC
+ *    and are only visible to the user running the app)
+ */
+const SENSITIVE_TRANSACTION_HEADERS = new Set([
+  'authorization',
+  'proxy-authorization',
+  'cookie',
+  'set-cookie',
+  'x-api-key',
+  'api-key',
+  'x-auth-token'
+]);
+
+const REDACTED_VALUE = '[REDACTED]';
+
+/**
+ * Headers whose value starts with an auth scheme (e.g. "Bearer xyz",
+ * "Basic xyz"). For these, the scheme is preserved and only the credential
+ * portion is redacted ("Bearer [REDACTED]"), which is useful for debugging
+ * client configuration without leaking the secret.
+ */
+const SCHEME_PRESERVING_HEADERS = new Set([
+  'authorization',
+  'proxy-authorization'
+]);
+
+const redactHeaderValue = (key: string, value: string): string => {
+  if (SCHEME_PRESERVING_HEADERS.has(key)) {
+    const [scheme, ...rest] = value.split(' ');
+
+    return rest.length === 0 ? REDACTED_VALUE : `${scheme} ${REDACTED_VALUE}`;
+  }
+
+  return REDACTED_VALUE;
+};
+
+/**
+ * Return a copy of the given header list with sensitive values replaced.
+ */
+export const redactHeaders = (headers: Header[]): Header[] =>
+  headers.map((header) => {
+    const lowerKey = header.key.toLowerCase();
+
+    return SENSITIVE_TRANSACTION_HEADERS.has(lowerKey)
+      ? { ...header, value: redactHeaderValue(lowerKey, header.value) }
+      : header;
+  });
+
+/**
+ * Return a shallow copy of a transaction with sensitive request/response
+ * header values redacted.
+ */
+export const redactTransaction = (transaction: Transaction): Transaction => ({
+  ...transaction,
+  request: {
+    ...transaction.request,
+    headers: redactHeaders(transaction.request.headers)
+  },
+  response: {
+    ...transaction.response,
+    headers: redactHeaders(transaction.response.headers)
+  }
+});
+
+/**
+ * Mutate the given in-flight request in place, redacting sensitive header
+ * values. The input is expected to be a clone (e.g. via CloneObject) so the
+ * underlying transaction reference held elsewhere stays unchanged.
+ */
+export const redactInFlightRequestInPlace = (
+  inflightRequest: InFlightRequest
+): InFlightRequest => {
+  if (inflightRequest.request?.headers) {
+    inflightRequest.request.headers = redactHeaders(
+      inflightRequest.request.headers
+    );
+  }
+
+  return inflightRequest;
+};
+
 /**
  * Transform http headers objects to Mockoon's Header key value object
  *
diff --git a/packages/commons/src/models/server.model.ts b/packages/commons/src/models/server.model.ts
index 7e900ea265bb9f52848ee2cf6a7c16254fcc3803..1defe2af7b16678671761bb026283353d30fbe1a 100644
--- a/packages/commons/src/models/server.model.ts
+++ b/packages/commons/src/models/server.model.ts
@@ -119,6 +119,20 @@ export type ServerOptions = {
    */
   enableAdminApi: boolean;
 
+  /**
+   * Bearer token required to access the admin API.
+   * If omitted, the runtime generates one automatically.
+   */
+  adminApiAuthToken?: string;
+
+  /**
+   * Explicit list of allowed CORS origins for the admin API (e.g. ['https://app.example.com']).
+   * - When empty/undefined, no CORS headers are emitted (default-deny browser cross-origin requests).
+   * - When a request's `Origin` header matches one of the entries, the origin is echoed back.
+   * - To explicitly opt into wildcard CORS, include `'*'` in the list.
+   */
+  adminApiCorsOrigins?: string[];
+
   /**
    * Disable TLS
    */
diff --git a/packages/commons/src/utils/utils.ts b/packages/commons/src/utils/utils.ts
index d04eca4dc65fc9c17746076f64ec7c02e315ac9b..5ffd463a698d35877bb0d34aba35fb1700be1955 100644
--- a/packages/commons/src/utils/utils.ts
+++ b/packages/commons/src/utils/utils.ts
@@ -182,6 +182,27 @@ export const generateUUID = (): string =>
     ? window.crypto.randomUUID()
     : require('crypto').randomUUID();
 
+/**
+ * Generate a cryptographically secure random token encoded in hexadecimal.
+ */
+export const generateSecureToken = (byteLength = 32): string => {
+  const effectiveByteLength = Math.max(1, Math.floor(byteLength));
+
+  const cryptoLib =
+    globalThis.crypto ?? require('crypto').webcrypto ?? undefined;
+
+  if (!cryptoLib) {
+    return require('crypto').randomBytes(effectiveByteLength).toString('hex');
+  }
+
+  const randomBytes = new Uint8Array(effectiveByteLength);
+  cryptoLib.getRandomValues(randomBytes);
+
+  return Array.from(randomBytes, (byte) =>
+    byte.toString(16).padStart(2, '0')
+  ).join('');
+};
+
 /**
  * Return a random integer
  *
@@ -514,3 +535,16 @@ export const pathMatchErrorBuilder = (error: unknown) => {
     message: 'Invalid route path'
   };
 };
+
+/**
+ * Extract a Bearer token from an Authorization header.
+ * Returns undefined when the header is not a Bearer scheme or token is empty.
+ */
+export const extractBearerToken = (
+  authorizationHeader: string | undefined
+): string | undefined => {
+  const headerValue = authorizationHeader ?? '';
+  const token = headerValue.replace(/^bearer\s+/i, '').trim();
+
+  return token !== headerValue.trim() && token ? token : undefined;
+};
diff --git a/packages/serverless/src/libs/serverless.ts b/packages/serverless/src/libs/serverless.ts
index f8ab91f2df5b821f59e0b013486a0f319ced551b..a16f5681c87086ce7bfd79a5d0abed65b583f3cb 100644
--- a/packages/serverless/src/libs/serverless.ts
+++ b/packages/serverless/src/libs/serverless.ts
@@ -12,8 +12,13 @@ import {
 import { RequestListener } from 'http';
 import ServerlessHttp from 'serverless-http';
 
+type ServerlessOptions = Partial<ServerOptions> & {
+  logTransaction: boolean;
+  adminApiAuthToken?: string;
+};
+
 export class MockoonServerless {
-  private options: Partial<ServerOptions> & { logTransaction: boolean } = {
+  private options: ServerlessOptions = {
     logTransaction: false,
     disabledRoutes: [],
     fakerOptions: {},
@@ -37,6 +42,15 @@ export class MockoonServerless {
       ...this.options,
       ...options
     };
+
+    this.options.adminApiAuthToken =
+      this.options.adminApiAuthToken ?? process.env['MOCKOON_ADMIN_API_TOKEN'];
+
+    if (this.options.enableAdminApi && !this.options.adminApiAuthToken) {
+      throw new Error(
+        'Admin API is enabled but no admin API token was provided. Set adminApiAuthToken or MOCKOON_ADMIN_API_TOKEN, or disable the admin API.'
+      );
+    }
   }
 
   /**
@@ -47,16 +61,19 @@ export class MockoonServerless {
    */
   public requestListener(): RequestListener {
     const logger = createLoggerInstance();
-    const server = new MockoonServer(this.environment, {
+    const serverOptions = {
       disabledRoutes: this.options.disabledRoutes,
       fakerOptions: this.options.fakerOptions,
       envVarsPrefix: this.options.envVarsPrefix,
       enableAdminApi: this.options.enableAdminApi,
+      adminApiAuthToken: this.options.adminApiAuthToken,
+      adminApiCorsOrigins: this.options.adminApiCorsOrigins,
       disableTls: this.options.disableTls,
       maxTransactionLogs: this.options.maxTransactionLogs,
       enableRandomLatency: this.options.enableRandomLatency,
       enableRouteMetadataHeaders: this.options.enableRouteMetadataHeaders
-    });
+    } as Partial<ServerOptions>;
+    const server = new MockoonServer(this.environment, serverOptions);
     listenServerEvents(
       server,
       this.environment,

# (16 test/doc file(s) of the upstream fix omitted here)

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### packages/app/src/main/libs/server-management.ts
```
import {
  Environment,
  Environments,
  InFlightRequest,
  ProcessedDatabucketWithoutValue,
  Transaction
} from '@mockoon/commons';
import { MockoonServer, listenServerEvents } from '@mockoon/commons-server';
import { dirname } from 'path';
import { mainLogger } from 'src/main/libs/logs';
import { getMainWindow } from 'src/main/libs/main-window';
import { getSettings } from 'src/main/libs/settings';

export class ServerInstance {
  private static instances: Record<string, ServerInstance> = {};
  private mockoonServer: MockoonServer | null = null;

  constructor(
    private environment: Environment,
    private environmentPath: string
  ) {
    ServerInstance.instances[this.environment.uuid] = this;
    this.start();
  }

  public static updateEnvironments = (environments: Environments) => {
    environments.forEach((environment) => {
      if (ServerInstance.instances[environment.uuid]?.mockoonServer) {
        ServerInstance.instances[
          environment.uuid
        ]?.mockoonServer?.updateEnvironment(environment);
      }
    });
  };

  public static updateDisabledRoutes = (
    disabledRoutes: Record<string, string[]>
  ) => {
    Object.keys(disabledRoutes).forEach((environmentUuid) => {
      if (ServerInstance.instances[environmentUuid]?.mockoonServer) {
        ServerInstance.instances[
          environmentUuid
        ]?.mockoonServer?.updateDisabledRoutes(disabledRoutes[environmentUuid]);
      }
    });
  };

  public static stop(environmentUuid: string) {
    ServerInstance.instances[environmentUuid]?.mockoonServer?.stop();
  }

  public static stopAll() {
    Object.keys(ServerInstance.instances).forEach((runningEnvironmentUuid) => {
      this.stop(runningEnvironmentUuid);
    });
  }

  public static getProcessedDatabucketValue(
    environmentUuid: string,
    databucketUuid: string
  ) {
    return ServerInstance.instances[
      environmentUuid
    ]?.mockoonServer?.getProcessedDatabucket(databucketUuid)?.value;
  }

  private start() {
    const mainWindow = getMainWindow();
    const environmentDirectory = dirname(this.environmentPath);
    const server = new MockoonServer(this.environment, {
      environmentDirectory,
      disabledRoutes:
        getSettings().disabledRoutes?.[this.environment.uuid] || [],
      fakerOptions: {
        seed: getSettings().fakerSeed,
        locale: getSettings().fakerLocale
      },
      envVarsPrefix: getSettings().envVarsPrefix,
      maxTransactionLogs: getSettings().maxLogsPerEnvironment,
      enableRandomLatency: getSettings().enableRandomLatency,
      enableRouteMetadataHeaders: true
    });

    listenServerEvents(
      server,
      this.environment,
      mainLogger(),
      getSettings().logTransactions
    );

    server.once('started', () => {
      this.mockoonServer = server;
      if (!mainWindow.isDestroyed()) {
        mainWindow.webContents.send(
          'APP_SERVER_EVENT',
          this.environment.uuid,
          'started'
        );
      }
    });

    server.once('stopped', () => {
      delete ServerInstance.instances[this.environment.uuid];

      // verify that window is still present as we stop servers when app quits too
      if (!mainWindow.isDestroyed()) {
        mainWindow.webContents.send(
          'APP_SERVER_EVENT',
          this.environment.uuid,
          'stopped'
        );

        return;
      }
    });

    server.on('entering-request', () => {
      if (!mainWindow.isDestroyed()) {
        mainWindow.webContents.send(
          'APP_SERVER_EVENT',
          this.environment.uuid,
          'entering-request'
        );
      }
    });

    server.on('ws-new-connection', (request: InFlightRequest) => {
      if (!mainWindow.isDestroyed()) {
        mainWindow.webContents.send(
          'APP_SERVER_EVENT',
          this.environment.uuid,
          'ws-new-connection',
          { inflightRequest: request }
        );
      }
    });

    server.on('transaction-complete', (transaction: Transaction) => {
      if (!mainWindow.isDestroyed()) {
        mainWindow.webContents.send(
          'APP_SERVER_EVENT',
          this.environment.uuid,
          'transaction-complete',
          { transaction }
        );
      }
    });

    server.on(
      'data-bucket-processed',
      (dataBuckets: ProcessedDatabucketWithoutValue[]) => {
        if (!mainWindow.isDestroyed()) {
          mainWindow.webContents.send(
            'APP_SERVER_EVENT',
            this.environment.uuid,
            'data-bucket-processed',
            { dataBuckets }
          );
        }
      }
    );

    server.on('error', (errorCode: any, originalError: any) => {
      if (!mainWindow.isDestroyed()) {
        mainWindow.webContents.send(
          'APP_SERVER_EVENT',
          this.environment.uuid,
          'error',
          {
            errorCode,
            originalError
          }
        );
      }
    });

    server.start();
  }
}

```

### packages/app/src/renderer/app/components/dropdown-menu/dropdown-menu.component.html
```
@let confirmRequested = confirmRequested$ | async;

<div
  class="h-100"
  ngbDropdown
  autoClose="outside"
  (openChange)="onChange($event)"
  #dropdownInstance="ngbDropdown"
  [id]="idPrefix() + '-dropdown'"
>
  <button
    class="btn dropdown-toggle h-100 d-flex align-items-center"
    [class]="{
      'btn-custom': label(),
      'btn-link': icon(),
      'btn-icon': icon(),
      'dropdown-toggle-icon': icon(),
      'dropdown-toggle-no-caret': icon(),
      'hover-fade': iconFaded(),
      'py-0': noYPadding()
    }"
    type="button"
    ngbDropdownToggle
    (click)="$event.stopPropagation()"
  >
    @if (icon()) {
      <app-svg [icon]="icon()" />
    }
    @if (label()) {
      <div class="dropdown-toggle-label">{{ label() }}</div>
    }
  </button>
  <div
    class="dropdown-menu"
    [class]="{ 'dropdown-menu-height-content': menuHeightFitContent() }"
    style="max-width: 40vw"
    [id]="idPrefix() + '-dropdown-menu'"
    ngbDropdownMenu
  >
    <div class="dropdown-menu-content">
      @for (item of items(); track $index) {
        @if (isSeparator(item)) {
          <hr class="dropdown-divider" />
        } @else if (isItem(item)) {
          @let itemLabel =
            typeof item.label === 'function'
              ? (item.label(payload()) | async)
              : item.label;
          @let itemIcon =
            typeof item.icon === 'function'
              ? (item.icon(payload()) | async)
              : item.icon;
          @let disabled = item.disabled$ && item.disabled$(payload()) | async;
          @let hidden = item.hidden$ && item.hidden$(payload()) | async;
          @let disabledLabel =
            item.disabledLabel$ && item.disabledLabel$(payload()) | async;
          @let needConfirm = item.twoSteps && confirmRequested.enabled;

          @if (!hidden) {
            <button
              class="btn dropdown-item d-flex"
              [class]="{
                'text-danger': needConfirm
              }"
              (click)="itemClicked(item, dropdownInstance)"
              [disabled]="disabled"
            >
              <span class="text-truncate">
                @if (item.icon) {
                  <app-svg
                    [icon]="needConfirm ? item.confirmIcon : itemIcon"
                    class="pe-2"
                  />
                }
                {{
                  needConfirm
                    ? item.confirmLabel
                    : disabled
                      ? disabledLabel || itemLabel
                      : itemLabel
                }}
                @if (item.subLabel) {
                  <br />
                  <small class="text-muted">{{ item.subLabel }}</small>
                }
              </span>
            </button>
          }
        }
      }
    </div>
  </div>
</div>

```

### packages/app/src/renderer/app/components/environment-settings/environment-settings.component.html
```
@let instanceUrl = instanceUrl$ | async;
@let activeEnvironment = activeEnvironment$ | async;
@let isActiveEnvironmentEditable = isActiveEnvironmentEditable$ | async;

@if (activeEnvironment) {
  <div class="d-flex flex-column h-100 p-2" [formGroup]="activeEnvironmentForm">
    <div class="input-group align-items-center">
      <label for="env-settings-name" class="pe-2">Name</label>
      <div class="col-4">
        <input
          type="text"
          class="form-control"
          formControlName="name"
          id="env-settings-name"
        />
      </div>
    </div>

    <app-title-separator
      [heading]="isWeb ? 'API prefix' : 'API URL'"
      icon="power"
      subheading="API available on {{
        instanceUrl +
          (activeEnvironment.endpointPrefix
            ? '/' + activeEnvironment.endpointPrefix
            : '')
      }}"
    />

    <div class="input-group align-items-center">
      @if (!isWeb) {
        <div class="col-1">
          <input
            type="text"
            class="form-control"
            id="env-settings-hostname"
            placeholder="localhost"
            formControlName="hostname"
          />
        </div>
        <div class="input-group-text">
          <span class="font-bold">:</span>
        </div>
        <div class="col-1">
          <input
            type="number"
            class="form-control"
            id="env-settings-port"
            placeholder="port"
            formControlName="port"
            [appInputNumber]="{
              min: 0,
              max: 65535,
              canBeEmpty: false
            }"
          />
        </div>
      }
      <div class="input-group-text">
        <span class="font-bold">/</span>
      </div>
      <div class="col-4">
        <input
          type="text"
          class="form-control"
          placeholder="prefix"
          appValidPath
          formControlName="endpointPrefix"
        />
      </div>
      @if (!isWeb) {
        <div class="input-group-text">
          <app-svg
            icon="info"
            ngbTooltip="Default hostname is :: (IPv6) and 0.0.0.0 (IPv4)"
          />
        </div>
      }
    </div>

    @if (!isWeb) {
      <app-title-separator
        heading="TLS"
        icon="lock"
        subheading="TLS uses a self-signed certificate by default"
      />

      <ng-container formGroupName="tlsOptions">
        <div class="input-group align-items-center">
          <div class="form-check">
            <input
              type="checkbox"
              class="form-check-input"
              id="env-settings-tls-enabled"
              formControlName="enabled"
            />
            <label class="form-check-label" for="env-settings-tls-enabled"
              >Enable TLS
            </label>
          </div>
        </div>

        <div class="mb-2 d-flex justify-content-center">
          <app-toggle
            class="me-3"
            prefix="cert-types"
            formControlName="type"
            [items]="certTypes"
            [uncheckable]="false"
          />
        </div>

        <div
          class="input-group align-items-center mb-2"
          id="tls-cert-container"
        >
          @if (
            activeEnvironmentForm.get(['tlsOptions', 'type']).value === 'PFX'
          ) {
            <label for="env-settings-tls-pfxPath" class="pe-2"
              >PFX or PKCS12 path</label
            >
            <div class="col-4">
              <input
                type="text"
                class="form-control"
                formControlName="pfxPath"
                id="env-settings-tls-pfxPath"
              />
            </div>
            <button
              class="btn btn-link"
              ngbTooltip="Browse files"
              (click)="browseFiles('pfxPath')"
              [disabled]="!isActiveEnvironmentEditable"
            >
              <app-svg icon="find_in_page" />
            </button>
          }
          @if (
            activeEnvironmentForm.get(['tlsOptions', 'type']).value === 'CERT'
          ) {
            <label for="env-settings-tls-certPath" class="pe-2 col-1"
              >Cert path</label
            >
            <input
              type="text"
              class="form-control"
              formControlName="certPath"
              id="env-settings-tls-certPath"
            />
            <button
              class="btn btn-link"
              ngbTooltip="Browse files"
              (click)="browseFiles('certPath')"
              [disabled]="!isActiveEnvironmentEditable"
            >
              <app-svg icon="find_in_page" />
            </button>
            <label for="env-settings-tls-keyPath" class="pe-2">Key path</label>
            <input
              type="text"
              class="form-control"
              formControlName="keyPath"
              id="env-settings-tls-keyPath"
            />
            <button
              class="btn btn-link"
              ngbTooltip="Browse files"
              (click)="browseFiles('keyPath')"
              [disabled]="!isActiveEnvironmentEditable"
            >
              <app-svg icon="find_in_page" />
            </button>
          }
        </div>

        <div class="input-group align-items-center">
          <label for="env-settings-tls-caPath" class="pe-2 col-1"
            >CA cert path</label
          >
          <input
            type="text"
            class="form-control"
            formControlName="caPath"
            id="env-settings-tls-caPath"
          />
          <button
            class="btn btn-link"
            ngbTooltip="Browse files"
            (click)="browseFiles('caPath')"
            [disabled]="!isActiveEnvironmentEditable"
          >
            <app-svg icon="find_in_page" />
          </button>
          <label for="env-settings-tls-passphrase" class="pe-2"
            >Cert passphrase</label
          >
          <input
            type="text"
            class="form-control"
            formControlName="passphrase"
            id="env-settings-tls-passphrase"
          />
        </div>
      </ng-container>
    }
    <app-title-separator heading="Misc" icon="storage" />

    <div class="input-group mb-3 align-items-center">
      <label for="env-settings-latency" class="col-form-label pe-2">
        Latency (ms)
      </label>
      <div class="col-1">
        <input
          type="number"
          id="env-settings-latency"
          class="form-control"
          formControlName="latency"
          [appInputNumber]="{
            min: 0,
            max: Infinity,
            canBeEmpty: false
          }"
        />
      </div>
      <div class="input-group-text">
        <app-svg
          icon="info"
          ngbTooltip="Global environment latency applied to all routes"
        />
      </div>
    </div>

    <div class="input-group align-items-center">
      <div class="form-check">
        <input
          type="checkbox"
          class="form-check-input"
          id="env-settings-cors"
          formControlName="cors"
        />
        <label class="form-check-label" for="env-settings-cors"
          >Automatically handle OPTIONS pre-flight requests
        </label>
      </div>
      <div class="input-group-text">
        <app-svg
          icon="info"
          ngbTooltip="Mockoon will now automatically answer with a 200 HTTP status code to
      all preflight OPTIONS requests"
        />
      </div>
    </div>
  </div>
}

```

### packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts
```
import { AsyncPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormsModule,
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormGroup
} from '@angular/forms';
import { Environment, EnvironmentDefault } from '@mockoon/commons';
import { NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { Observable, combineLatest, merge } from 'rxjs';
import { filter, map, tap } from 'rxjs/operators';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import { TitleSeparatorComponent } from 'src/renderer/app/components/title-separator/title-separator.component';
import { ToggleComponent } from 'src/renderer/app/components/toggle/toggle.component';
import { InputNumberDirective } from 'src/renderer/app/directives/input-number.directive';
import { ValidPathDirective } from 'src/renderer/app/directives/valid-path.directive';
import { buildApiUrl } from 'src/renderer/app/libs/utils.lib';
import { ToggleItems } from 'src/renderer/app/models/common.model';
import { DialogsService } from 'src/renderer/app/services/dialogs.service';
import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';

@Component({
  selector: 'app-environment-settings',
  templateUrl: './environment-settings.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    TitleSeparatorComponent,
    InputNumberDirective,
    ValidPathDirective,
    SvgComponent,
    NgbTooltip,
    ToggleComponent,
    AsyncPipe
  ]
})
export class EnvironmentSettingsComponent {
  private formBuilder = inject(UntypedFormBuilder);
  private environmentsService = inject(EnvironmentsService);
  private store = inject(Store);
  private dialogsService = inject(DialogsService);
  public activeEnvironment$: Observable<Environment>;
  public instanceUrl$: Observable<string>;
  public activeEnvironmentForm: UntypedFormGroup;
  public Infinity = Infinity;
  public certTypes: ToggleItems = [
    {
      value: 'CERT',
      label: 'CERT'
    },
    {
      value: 'PFX',
      label: 'PFX'
    }
  ];
  public isWeb = Config.isWeb;
  public isActiveEnvironmentEditable$ = this.store
    .selectIsActiveEnvironmentEditable()
    .pipe(
      tap((isEditable) => {
        if (isEditable) {
          this.activeEnvironmentForm.enable({ emitEvent: false });
        } else {
          this.activeEnvironmentForm.disable({ emitEvent: false });
        }
      })
    );

  constructor() {
    this.activeEnvironment$ = this.store.selectActiveEnvironment();
    this.instanceUrl$ = combineLatest([
      this.activeEnvironment$,
      this.store.select('deployInstances')
    ]).pipe(
      map(([environment, deployInstances]) => {
        const instance = deployInstances.find(
          (deployInstance) =>
            deployInstance.environmentUuid === environment.uuid
        );

        const urls = buildApiUrl({ environment, instance });

        return this.isWeb ? urls.webUrl : urls.localUrl;
      })
    );

    this.activeEnvironmentForm = this.formBuilder.group({
      name: [EnvironmentDefault.name],
      hostname: [EnvironmentDefault.hostname],
      port: [EnvironmentDefault.port],
      endpointPrefix: [EnvironmentDefault.endpointPrefix],
      latency: [EnvironmentDefault.latency],
      tlsOptions: this.formBuilder.group({
        enabled: [EnvironmentDefault.tlsOptions.enabled],
        type: [EnvironmentDefault.tlsOptions.type],
        pfxPath: [EnvironmentDefault.tlsOptions.pfxPath],
        certPath: [EnvironmentDefault.tlsOptions.certPath],
        keyPath: [EnvironmentDefault.tlsOptions.keyPath],
        caPath: [EnvironmentDefault.tlsOptions.caPath],
        passphrase: [EnvironmentDefault.tlsOptions.passphrase]
      }),
      cors: [EnvironmentDefault.cors]
    });

    // send new activeEnvironmentForm values to the store, one by one
    merge(
      ...Object.keys(this.activeEnvironmentForm.controls).map((controlName) =>
        this.activeEnvironmentForm.get(controlName).valueChanges.pipe(
          map((newValue) => ({
            [controlName]: newValue
          }))
        )
      )
    )
      .pipe(
        tap((newProperty) => {
          this.environmentsService.updateActiveEnvironment(newProperty);
        }),
        takeUntilDestroyed()
      )
      .subscribe();

    // subscribe to active environment changes to reset the form
    this.activeEnvironment$
      .pipe(
        filter((environment) => !!environment),
        this.store.distinctUUIDOrForce(),
        tap((activeEnvironment) => {
          this.activeEnvironmentForm.setValue(
            {
              name: activeEnvironment.name,
              hostname: activeEnvironment.hostname,
              port: activeEnvironment.port,
              endpointPrefix: activeEnvironment.endpointPrefix,
              latency: activeEnvironment.latency,
              tlsOptions: activeEnvironment.tlsOptions,
              cors: activeEnvironment.cors
            },
            { emitEvent: false }
          );
        }),
        takeUntilDestroyed()
      )
      .subscribe();
  }

  /**
   * Open file browsing dialog
   */
  public browseFiles(target: string) {
    this.dialogsService
      .showOpenDialog('Choose a file', null, false)
      .pipe(
        tap((filePaths) => {
          if (filePaths[0]) {
            this.activeEnvironmentForm
              .get(['tlsOptions', target])
              .setValue(filePaths[0]);
          }
        })
      )
      .subscribe();
  }
}

```

### packages/app/src/renderer/app/models/main-api.model.ts
```
import {
  Environment,
  Environments,
  InFlightRequest,
  ProcessedDatabucketWithoutValue,
  ServerErrorCodes,
  ServerEvents,
  Transaction
} from '@mockoon/commons';
import {
  OpenDialogOptions,
  OpenDialogReturnValue,
  SaveDialogOptions,
  SaveDialogReturnValue,
  app
} from 'electron';
import { MenuStateUpdatePayload } from 'src/shared/models/ipc.model';
import {
  EnvironmentDescriptor,
  Settings
} from 'src/shared/models/settings.model';

export interface MainAPIModel {
  invoke(
    channel: 'APP_READ_ENVIRONMENT_DATA',
    path: string
  ): Promise<Environment>;
  invoke(channel: 'APP_READ_SETTINGS_DATA'): Promise<Settings>;
  invoke(
    channel: 'APP_WRITE_ENVIRONMENT_DATA',
    data: Environment,
    descriptor: EnvironmentDescriptor,
    storagePrettyPrint?: boolean
  ): Promise<void>;
  invoke(channel: 'APP_DELETE_ENVIRONMENT_DATA', path: string): Promise<void>;
  invoke(
    channel: 'APP_WRITE_SETTINGS_DATA',
    newSettings: Settings,
    storagePrettyPrint?: boolean
  ): Promise<void>;
  invoke(channel: 'APP_READ_CLIPBOARD'): Promise<any>;
  invoke(
    channel: 'APP_SHOW_OPEN_DIALOG',
    options: OpenDialogOptions
  ): Promise<OpenDialogReturnValue>;
  invoke(
    channel: 'APP_SHOW_SAVE_DIALOG',
    options: SaveDialogOptions
  ): Promise<SaveDialogReturnValue>;
  invoke(
    channel:
      | 'APP_GET_MIME_TYPE'
      | 'APP_GET_HASH'
      | 'APP_GET_FILENAME'
      | 'APP_READ_FILE'
      | 'APP_BUILD_STORAGE_FILEPATH'
      | 'APP_GET_BASE_PATH'
      | 'APP_REPLACE_FILEPATH_EXTENSION',
    pathOrNameOrString: string
  ): Promise<string>;
  invoke(channel: 'APP_WRITE_FILE', path: string, data: string): Promise<void>;
  invoke(
    channel: 'APP_SERVER_GET_PROCESSED_DATABUCKET_VALUE',
    environmentUuid: string,
    databucketUuid: string
  ): Promise<any>;
  invoke(
    channel: 'APP_START_SERVER',
    environment: Environment,
    environmentPath: string
  ): Promise<any>;
  invoke(
    channel: 'APP_STOP_SERVER' | 'APP_UNWATCH_FILE',
    uuid: string
  ): Promise<void>;
  invoke(channel: 'APP_GET_OS'): Promise<NodeJS.Platform>;
  invoke(channel: 'APP_UNWATCH_ALL_FILE'): Promise<void>;

  send(channel: 'APP_UPDATE_MENU_STATE', state: MenuStateUpdatePayload): void;
  send(channel: 'APP_WRITE_CLIPBOARD', data: any): void;
  send(
    channel:
      | 'APP_QUIT'
      | 'APP_HIDE_WINDOW'
      | 'APP_APPLY_UPDATE'
      | 'APP_AUTH_STOP_SERVER'
      | 'APP_AUTH'
  ): void;
  send(
    channel: 'APP_SHOW_FILE' | 'APP_OPEN_FILE',
    path: string,
    relativeToFile?: string
  ): void;
  send(
    channel: 'APP_SHOW_FOLDER',
    path: Parameters<typeof app.getPath>[0]
  ): void;
  send(
    channel: 'APP_LOGS',
    data: { type: 'error' | 'info'; message: string; payload?: any }
  ): void;
  send(channel: 'APP_UPDATE_ENVIRONMENTS', environments: Environments): void;
  send(
    channel: 'APP_UPDATE_DISABLED_ROUTES',
    disabledRoutes: Record<string, string[]>
  ): void;
  send(channel: 'APP_ZOOM', action: 'IN' | 'OUT' | 'RESET'): void;

  receive(
    channel: 'APP_SERVER_EVENT',
    listener: (
      environmentUUID: string,
      eventName: keyof ServerEvents,
      data: {
        errorCode?: ServerErrorCodes;
        originalError?: Error;
        transaction?: Transaction;
        inflightRequest?: InFlightRequest;
        dataBuckets?: ProcessedDatabucketWithoutValue[];
      }
    ) => void
  ): void;
  receive(channel: 'APP_MENU', listener: (action: string) => void): void;
  receive(
    channel: 'APP_UPDATE_AVAILABLE',
    listener: (version: string) => void
  ): void;
  receive(
    channel: 'APP_AUTH_CALLBACK',
    listener: (token: string) => void
  ): void;
  receive(
    channel: 'APP_CUSTOM_PROTOCOL',
    listener:
      | ((action: 'load-environment', parameters: { url: string }) => void)
      | ((action: 'auth', parameters: { token: string }) => void)
  ): void;

  receive(
    channel: 'APP_FILE_EXTERNAL_CHANGE',
    listener: (previousUUID: string, environmentPath: string) => void
  ): void;
}

```

### packages/app/src/renderer/app/models/store.model.ts
```
import {
  DeployInstance,
  RemoteConfigData,
  SyncPresence,
  User
} from '@mockoon/cloud';
import {
  Environments,
  ProcessedDatabucketWithoutValue
} from '@mockoon/commons';
import {
  CallbackSpecTabNameType,
  CallbackTabsNameType
} from 'src/renderer/app/models/callback.model';
import { DataSubject } from 'src/renderer/app/models/data.model';
import {
  ActiveEnvironmentsLogUUIDs,
  EnvironmentLogs
} from 'src/renderer/app/models/environment-logs.model';
import { OpenApiReimportPlan } from 'src/renderer/app/models/openapi.model';
import { Toast } from 'src/renderer/app/models/toasts.model';
import { Settings } from 'src/shared/models/settings.model';

export type ViewsNameType =
  | 'ENV_ROUTES'
  | 'ENV_DATABUCKETS'
  | 'ENV_HEADERS'
  | 'ENV_LOGS'
  | 'ENV_PROXY'
  | 'ENV_SETTINGS'
  | 'ENV_CALLBACKS';

export type TabsNameType =
  | 'RESPONSE'
  | 'HEADERS'
  | 'RULES'
  | 'SETTINGS'
  | 'CALLBACKS';

export type CallbackSettings = {
  activeTab: CallbackTabsNameType;
  activeSpecTab: CallbackSpecTabNameType;
};

export type EnvironmentLogsTabsNameType = 'REQUEST' | 'RESPONSE';

export type TemplatesTabsName =
  | 'LIST'
  | 'GENERATE_TEMPLATE'
  | 'GENERATE_ENDPOINT';

export type EnvironmentStatus = {
  running: boolean;
  needRestart: boolean;
  redeploying: boolean;
};

export type EnvironmentsStatuses = Record<string, EnvironmentStatus>;

export type DuplicatedRoutesTypes = Record<string, Set<string>>;

export type UIState = {
  closing: boolean;
  saving: boolean;
};

export type DuplicateEntityToAnotherEnvironment = {
  moving: boolean;
  subject?: Omit<DataSubject, 'environment' | 'folder'>;
  // UUIDs of the entities to duplicate. Always an array; contains a single
  // element for the standard single-entity flow, multiple for batch flows
  // (currently only supported for routes).
  subjectUuids?: string[];
  targetEnvironmentUUID?: string;
};

export type StoreType = {
  activeTab: TabsNameType;
  activeView: ViewsNameType;
  activeEnvironmentLogsTab: EnvironmentLogsTabsNameType;
  activeTemplatesTab: TemplatesTabsName;
  activeEnvironmentUUID: string;
  activeRouteUUID: string;
  activeRouteResponseUUID: string;
  activeCallbackUUID: string;
  activeDatabucketUUID: string;
  environments: Environments;
  environmentsStatus: EnvironmentsStatuses;
  bodyEditorConfig: any;
  // duplicated routes per environment
  duplicatedRoutes: DuplicatedRoutesTypes;
  environmentsLogs: EnvironmentLogs;
  // the active log UUID per environment
  activeEnvironmentLogsUUID: ActiveEnvironmentsLogUUIDs;
  toasts: Toast[];
  uiState: UIState;
  settings: Settings;
  duplicateEntityToAnotherEnvironment: DuplicateEntityToAnotherEnvironment;
  filters: {
    routes: string;
    databuckets: string;
    templates: string;
    callbacks: string;
    logs: string;
    routeResponses: string;
  };
  user: User;
  callbackSettings: CallbackSettings;
  sync: {
    status: boolean;
    lastDisconnectedAt: number | null;
    presence: SyncPresence;
    offlineReason: string | null;
    alert: string | null;
  };
  deployInstances: DeployInstance[];
  /**
   * Processed databuckets data per environment, indexed by databucket UUID
   */
  processedDatabuckets: Record<
    string,
    Record<string, ProcessedDatabucketWithoutValue>
  >;
  feedback: string;
  remoteConfig: RemoteConfigData;
  openApiImport: {
    reimportPlan: OpenApiReimportPlan;
  };
};

```

### packages/app/src/renderer/app/services/server.service.ts
```
import { HttpClient } from '@angular/common/http';
import { inject, Injectable, NgZone } from '@angular/core';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { DeployInstance } from '@mockoon/cloud';
import {
  Environment,
  ProcessedDatabucket,
  ProcessedDatabucketWithoutValue,
  ServerEvents,
  Transaction
} from '@mockoon/commons';
import {
  catchError,
  delay,
  EMPTY,
  filter,
  from,
  map,
  merge,
  Subject,
  switchMap,
  tap
} from 'rxjs';
import { EnvironmentLogOrigin } from 'src/renderer/app/models/environment-logs.model';
import { MessageParams } from 'src/renderer/app/models/messages.model';
import { EventsService } from 'src/renderer/app/services/events.service';
import { LoggerService } from 'src/renderer/app/services/logger-service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import {
  updateEnvironmentStatusAction,
  updateProcessedDatabucketsAction
} from 'src/renderer/app/stores/actions';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';

@Injectable({ providedIn: 'root' })
export class ServerService {
  private store = inject(Store);
  private zone = inject(NgZone);
  private eventsService = inject(EventsService);
  private mainApiService = inject(MainApiService);
  private loggerService = inject(LoggerService);
  private httpClient = inject(HttpClient);

  private activeSseConnections = new Map<
    string,
    { subject: Subject<string>; abortController: AbortController }
  >();

  /**
   * Listen to SSE coming from the currently active environment admin API
   */
  public init() {
    this.mainApiService.receive(
      'APP_SERVER_EVENT',
      (environmentUuid, eventName, data) => {
        this.processEvent(environmentUuid, eventName, data, 'local');
      }
    );

    // listen to deployed instances events, both on desktop and web
    return this.store.select('deployInstances').pipe(
      filter((instances) => !!instances),
      tap((instances) => {
        const currentInstanceIds = instances.map(
          (instance) => instance.environmentUuid
        );

        // Stop and remove SSE connections for instances that no longer exist
        this.activeSseConnections.forEach((connection, instanceId) => {
          if (!currentInstanceIds.includes(instanceId)) {
            this.removeInstanceEventsListener(instanceId);
          }
        });
      }),
      filter((instances) => instances.length > 0),
      delay(3000), // Delay to ensure all instances are up before listening
      tap((instances) => {
        // Start or renew SSE for instances
        instances.forEach((instance) => {
          const existingConnection = this.activeSseConnections.get(
            instance.environmentUuid
          );

          if (existingConnection) {
            // Close the existing connection and replace it with a new one (re-deploy)
            this.removeInstanceEventsListener(instance.environmentUuid);
          }

          this.listenInstanceEvents(instance);
        });
      }),
      switchMap(() => {
        return merge(
          Array.from(this.activeSseConnections.entries()).map(
            ([environmentUuid, activeSseConnection]) =>
              activeSseConnection.subject.pipe(
                map((message) => ({ environmentUuid, message }))
              )
          )
        );
      }),
      tap((messages) => {
        messages.forEach(({ environmentUuid, message }) => {
          const payload: {
            event: keyof ServerEvents;
            transaction?: Transaction;
            dataBuckets?: ProcessedDatabucketWithoutValue[];
          } = JSON.parse(message as string);

          this.processEvent(environmentUuid, payload.event, payload, 'cloud');
        });
      }),
      catchError(() => {
        return EMPTY;
      })
    );
  }

  /**
   * Send the new environment configuration to the instance admin API
   *
   * @param environments
   * @returns
   */
  public updateRemoteServerEnvironments(environments: Environment[]) {
    if (environments.length === 0) {
      return;
    }

    const instances = this.store
      .get('deployInstances')
      .filter((deployInstance) =>
        environments.find(
          (environment) =>
            environment.uuid === deployInstance.environmentUuid &&
            deployInstance.liveUpdate
        )
      );

    if (!instances.length) {
      return;
    }

    instances.forEach((instance) => {
      this.httpClient
        .put(
          `${this.buildRemoteInstanceUrl(instance)}/environment`,
          environments.find(
            (environment) => environment.uuid === instance.environmentUuid
          ),
          {
            headers: { Authorization: `Bearer ${instance.apiKey}` }
          }
        )
        .pipe(catchError(() => EMPTY))
        .subscribe();
    });
  }

  /**
   * Start an environment/server
   *
   * @param environment
   */
  public async start(environment: Environment, environmentPath: string) {
    this.mainApiService.invoke(
      'APP_START_SERVER',
      environment,
      environmentPath
    );
  }

  /**
   * Completely stop an environment/server
   *
   * @param environmentUuid
   */
  public stop(environmentUuid: string) {
    this.mainApiService.invoke('APP_STOP_SERVER', environmentUuid);
  }

  /**
   * Get the processed value of a databucket from the local server
   * or from the remote admin API
   *
   * @param activeEnvironmentUuid
   * @param databucketUuid
   */
  public getProcessedDatabucketValue(
    activeEnvironmentUuid: string,
    databucketUuid: string
  ) {
    if (Config.isWeb) {
      const activeEnvironmentInstance = this.store
        .get('deployInstances')
        .find((instance) => instance.environmentUuid === activeEnvironmentUuid);

      if (!activeEnvironmentInstance) {
        return EMPTY;
      }

      return this.httpClient
        .get<ProcessedDatabucket>(
          `${this.buildRemoteInstanceUrl(activeEnvironmentInstance)}/data-buckets/${databucketUuid}`,
          {
            headers: {
              Authorization: 'Bearer ' + activeEnvironmentInstance.apiKey
            }
          }
        )
        .pipe(map((response) => response.value));
    } else {
      return from(
        this.mainApiService.invoke(
          'APP_SERVER_GET_PROCESSED_DATABUCKET_VALUE',
          activeEnvironmentUuid,
          databucketUuid
        )
      );
    }
  }

  /**
   * Start listening to SSE events from the remote instance
   *
   * @param instance
   * @param sseSubject
   */
  private listenInstanceEvents(instance: DeployInstance) {
    const abortController = new AbortController();
    const maxLogs = this.store.get('settings').maxLogsPerEnvironment;

    this.activeSseConnections.set(instance.environmentUuid, {
      subject: new Subject<string>(),
      abortController
    });

    const sseSubject = this.activeSseConnections.get(
      instance.environmentUuid
    )?.subject;

    try {
      fetchEventSource(
        `${this.buildRemoteInstanceUrl(instance)}/events?maxlogs=${maxLogs}`,
        {
          headers: { Authorization: `Bearer ${instance.apiKey}` },
          signal: abortController.signal,
          openWhenHidden: true,
          async onopen(response) {
            if (
              response.status >= 400 &&
              response.status < 500 &&
              response.status !== 429
            ) {
              abortController.abort();
              sseSubject.complete();
            }
          },
          onmessage(message) {
            // Do not process empty messages (pings)
            if (!message.data) {
              return;
            }

            sseSubject.next(message.data);
          }
        }
      );
    } catch (_error) {}
  }

  private removeInstanceEventsListener(environmentUuid: string) {
    const connection = this.activeSseConnections.get(environmentUuid);

    if (connection) {
      connection.abortController.abort();
      connection.subject.complete();
      this.activeSseConnections.delete(environmentUuid); // Remove from the map
    }
  }

  private processEvent(
    environmentUuid: string,
    eventName: string,
    data: any,
    origin: EnvironmentLogOrigin
  ) {
    const environment = this.store.getEnvironmentByUUID(environmentUuid);

    if (!environment) {
      return;
    }

    const loggerMessageParams: MessageParams = {
      port: environment.port,
      uuid: environment.uuid,
      hostname: environment.hostname,
      proxyHost: environment.proxyHost
    };

    switch (eventName) {
      case 'started':
        this.zone.run(() => {
          this.store.update(
            updateEnvironmentStatusAction(
              { running: true, needRestart: false },
              environment.uuid
            )
          );
        });
        break;

      case 'stopped':
        this.zone.run(() => {
          this.store.update(
            updateEnvironmentStatusAction(
              {
                running: false,
                needRestart: false
              },
              environment.uuid
            )
          );

          this.store.update(
            updateProcessedDatabucketsAction(environmentUuid, null)
          );
        });
        break;

      case 'ws-new-connection':
        if (data.inflightRequest) {
          this.zone.run(() => {
            this.eventsService.serverTransaction$.next({
              environmentUUID: environmentUuid,
              inflightRequest: data.inflightRequest,
              origin
            });
          });
        }
        break;

      case 'transaction-complete':
        if (data.transaction) {
          this.zone.run(() => {
            this.eventsService.serverTransaction$.next({
              environmentUUID: environmentUuid,
              transaction: data.transaction,
              origin
            });
          });
        }
        break;

      case 'data-bucket-processed':
        if (data.dataBuckets) {
          this.zone.run(() => {
            this.store.update(
              updateProcessedDatabucketsAction(
                environmentUuid,
                data.dataBuckets
              )
            );
          });
        }
        break;

      case 'error':
        this.loggerService.logMessage('error', data.errorCode, {
          error: data.originalError,
          ...loggerMessageParams
        });
        break;
      default:
        break;
    }
  }

  /**
   * Use .appdev locally (in your hosts file, see API docs for more info)
   * as .app always requires HTTPS (due to HSTS mechanism)
   *
   * @param instance
   * @returns
   */
  private buildRemoteInstanceUrl(instance: DeployInstance) {
    return `${instance.url}/mockoon-admin`;
  }
}

```

### packages/app/src/shared/shared-config.ts
```
import { defaultMaxTransactionLogs } from '@mockoon/commons';

const appVersion: string = require('../../package.json').version;

/**
 * Share config between main and renderer processes
 * Shouldn't be imported directly, use each Config file instead
 *
 * @param options
 * @returns
 */
export const SharedConfig = (options: {
  websiteURL: string;
  apiURL: string;
  isWeb?: boolean;
}) => {
  const docsUrl = `${options.websiteURL}docs/latest/`;
  const cloudDocsUrl = `${options.websiteURL}cloud/docs/`;

  return {
    isWeb: options.isWeb,
    appVersion,
    remoteConfigDefaults: {
      dataRefreshInterval: 300_000 // 5 minutes
    },
    websiteURL: options.websiteURL,
    apiURL: options.apiURL,
    githubBinaryURL: 'https://github.com/mockoon/mockoon/releases/download/',
    latestReleaseDataURL: `${options.apiURL}releases/desktop/stable.json`,
    changelogMarkdownURL: `${options.websiteURL}desktop-changelogs-markdown/`,
    releasePublicURL: `${options.websiteURL}releases/`,
    docs: {
      templating: `${docsUrl}templating/overview/`,
      proxy: `${docsUrl}server-configuration/proxy-mode/`,
      cors: `${docsUrl}server-configuration/cors/`,
      https: `${docsUrl}server-configuration/serving-over-tls/`,
      headers: `${docsUrl}response-configuration/response-headers/`,
      rules: `${docsUrl}route-responses/multiple-responses/`,
      hostname: `${docsUrl}server-configuration/listening-hostname/`,
      faq: `${options.websiteURL}faq/`,
      cloudOverview: `${cloudDocsUrl}about/`,
      cloudDeploy: `${cloudDocsUrl}api-mock-cloud-deployments/`,
      cloudSync: `${cloudDocsUrl}data-synchronization-team-collaboration/`,
      cloudDeployCliPull: `${cloudDocsUrl}api-mock-cloud-deployments/#self-host-with-the-cli`
    },
    // URLs should not be used directly in desktop app (but there is a redirection for the web app in user service). Instead use the flow methods in the user service
    appAuthURL: `${options.websiteURL}app-auth/`,
    loginURL: `${options.websiteURL}login/`,
    accountUrl: `${options.websiteURL}account/subscription/`,
    accountAuthenticationUrl: `${options.websiteURL}account/access-tokens/`,
    cloudPlansURL: `${options.websiteURL}cloud/`,
    maxPromptLength: 500,
    defaultMaxLogsPerEnvironment: defaultMaxTransactionLogs,
    maxLogsPerEnvironmentLimit: 1_000,
    defaultMainMenuSize: 100,
    defaultSecondaryMenuSize: 200,
    storageSaveDelay: 1000, // ms
    fileReWatchDelay: 3000, // ms
    firebaseConfig: {
      apiKey: 'AIzaSyCIkzTtimLebXjf-gfCQ6iwCVFsYRhCRvs',
      authDomain: 'mockoon-ba3e2.firebaseapp.com',
      databaseURL: 'https://mockoon-ba3e2.firebaseio.com',
      projectId: 'mockoon-ba3e2',
      storageBucket: 'mockoon-ba3e2.appspot.com',
      messagingSenderId: '902702764744',
      appId: '1:902702764744:web:599e8dc8d6a1ef6542cbfd'
    },
    recaptchaSiteKey: '6LfhRCErAAAAACwFRV5bcqMtNylLhp764ZWXJB90'
  };
};

```

### packages/cli/README.md
```
<div align="center">
  <a href="https://mockoon.com" alt="mockoon logo">
    <img width="200" height="200" src="https://mockoon.com/images/logo-square-cli.png">
  </a>
  <br>
  <a href="https://mockoon.com/download/"><img src="https://img.shields.io/badge/Download%20app-Go-green.svg?style=flat-square&colorB=1997c6"/></a>
  <a href="https://mockoon.com/"><img src="https://img.shields.io/badge/Website-Go-green.svg?style=flat-square&colorB=1997c6"/></a>
  <a href="https://mockoon.com/newsletter/"><img src="https://img.shields.io/badge/Newsletter-Subscribe-green.svg?style=flat-square"/></a>
  <br>
  <a href="https://www.npmjs.com/package/@mockoon/cli"><img src="https://img.shields.io/npm/v/@mockoon/cli.svg?style=flat-square&colorB=cb3837"/></a>
  <br>
  <br>
  <h1>@Mockoon/cli</h1>
</div>

Welcome to Mockoon's official CLI, a lightweight and fast NPM package to deploy your mock APIs anywhere.
Feed it with a Mockoon's [data file](https://mockoon.com/docs/latest/mockoon-data-files/data-files-location/), or OpenAPI specification file (JSON or YAML), and you are good to go.

The CLI supports the same features as the main application: [templating system](https://mockoon.com/docs/latest/templating/overview/), [proxy mode](https://mockoon.com/docs/latest/server-configuration/proxy-mode/), [route response rules](https://mockoon.com/docs/latest/route-responses/dynamic-rules/), etc.

![Mockoon CLI screenshot](https://mockoon.com/images/cli-hero-repo.png)

- [Installation](#installation)
- [Run a mock API with the CLI](#run-a-mock-api-with-the-cli)
  - [Use your Mockoon environment file](#use-your-mockoon-environment-file)
  - [Use an OpenAPI specification file](#use-an-openapi-specification-file)
- [Compatibility](#compatibility)
- [Commands](#commands)
  - [Start command](#start-command)
  - [Dockerize command](#dockerize-command)
  - [Import command](#import-command)
  - [Export command](#export-command)
  - [Help command](#help-command)
- [Use the GitHub Action](#use-the-github-action)
- [Docker image](#docker-image)
  - [Using the generic Docker image](#using-the-generic-docker-image)
  - [Using the `dockerize` command](#using-the-dockerize-command)
- [Logs](#logs)
- [Mockoon's documentation](#mockoons-documentation)
- [Sponsors](#sponsors)
- [Support/feedback](#supportfeedback)
- [Contributing](#contributing)
- [Roadmap](#roadmap)

## Installation

```sh-session
$ npm install -g @mockoon/cli
```

Usage:

```sh-session
$ mockoon-cli COMMAND
```

## Changelogs

You will find Mockoon applications [changelogs](https://mockoon.com/releases/) on the official website.

## Run a mock API with the CLI

### Use your Mockoon environment file

The CLI can import and migrate data from older versions of Mockoon. However, it doesn't alter the file you provide and only migrates a copy. If you created your mock with a more recent version of the application, you need to update your CLI with the following command: `npm install -g @mockoon/cli`.

You can run your mock in one single step using the [start command](#mockoon-cli-start) and replacing `~/path/to/your-environment-file.json` by the actual location of your Mockoon environment file:

```sh-sessions
$ mockoon-cli start --data ~/path/to/your-environment-file.json
```

> To locate your environment file from the main application, right-click on a environment and select "Show in folder" in the context menu:
> ![context menu - show in folder](https://mockoon.com/images/docs/repo/cli/environment-show-in-folder.png)

You can also directly load Mockoon's environment file from a URL. To do so, provide the URL as the `data` parameter instead of a local path:

```sh-sessions
$ mockoon-cli start --data https://domain.com/your-environment-file.json
```

### Run a cloud-hosted Mockoon environment

Since v9.5.0, you can also run a cloud-hosted Mockoon environment directly from the CLI by providing the cloud URL as the `data` parameter:

```sh-sessions
$ mockoon-cli start --data cloud://{UUID} --token {TOKEN}
```

Where `{UUID}` is your environment's UUID and `{TOKEN}` is your Mockoon Cloud [access token](https://mockoon.com/cloud/docs/access-tokens/).

The application will provide you with the necessary **commands and instructions** to set up and run the mock on your own servers in the environment dropdown menu:

![application dialog showing instructions to pull a cloud environment](https://mockoon.com/images/docs/repo/cli/cli-pull-instructions.png)

Learn more about self-hosting cloud environments in the [official Mockoon Cloud documentation](https://mockoon.com/cloud/docs/api-mock-cloud-deployments/#self-host-with-the-cli).


### Use an OpenAPI specification file

Another option is to directly pass an OpenAPI specification file as the `data` parameter. Mockoon supports both JSON and YAML formats in versions 2.0.0 and 3.0.0.

> ⚠️ There is currently no equivalent between all the OpenAPI specifications and Mockoon's features ([more info](https://mockoon.com/docs/latest/openapi/openapi-specification-compatibility/)). If you want to run your Mockoon mock APIs with the CLI with all the features (templating, rules, etc.), you must use Mockoon's data files ([see above](#use-your-mockoon-environment-file)) directly, or you may lose part of your mock's behavior.

You can provide a path to a local OpenAPI specification file or directly the file's URL:

```sh-sessions
$ mockoon-cli start --data ~/path/to/your-opeanapi-file.yaml
```

Or,

```sh-sessions
$ mockoon-cli start --data https://domain.com/your-opeanapi-file.yaml
```

## Compatibility

Mockoon's CLI has been tested on Node.js versions 18, 20, 22 and 24.

## Commands

- [`start`](#start-command)
- [`dockerize`](#dockerize-command)
- [`import`](#import-command)
- [`export`](#export-command)
- [`validate`](#validate-command)
- [`help`](#help-command)

### `start` command

Starts one (or more) mock API from Mockoon's environment file(s) as a foreground process.

The mocks will run by default on the ports and hostnames specified in the files. You can override these values by using the `--port` and `--hostname` flags.
`--data`, `--port`, `--hostname`, and `--public-base-url` flags support multiple entries to run multiple mock APIs at once (see examples below).

> 💡 To run the CLI as a background process, add an `&` at the end of the command: `mockoon-cli start -d ./data-file.json &`.

**Usage**:
`$ mockoon-cli start`

**Options**:
|Flag|Description|
|-|-|
|-d, --data |[required] Path(s) or URL(s) to your Mockoon file(s). Supports cloud URLs (e.g. `cloud://`, [see above](#run-a-cloud-hosted-mockoon-environment)).|
|-p, --port |Override environment(s) port(s)|
|-l, --hostname |Override default listening hostname(s)|
|-c, --faker-locale | Faker locale (e.g. 'en', 'en_GB', etc. For supported locales, see below.)|
|-s, --faker-seed | Number for the Faker.js seed (e.g. 1234)|
|-t, --log-transaction | Log the full HTTP transaction (request and response)|
|-X, --disable-log-to-file | Disable logging to file|
|-e, --disable-routes | Disable route(s) by UUID or keyword present in the route's path (do not include a leading slash) or keyword present in a folder name. Use '\*' to disable all routes.|
|-r, --repair | If the data file seems too old, or an invalid Mockoon file, migrate/repair without prompting|
|-x, --env-vars-prefix | Prefix for environment variables (default: 'MOCKOON\_')|
|-w, --watch | Watch local data file(s) for changes and restart the server when a change is detected (watch is using polling, see `--polling-interval` flag below)|
|--polling-interval | Local files watch polling interval in milliseconds (default: 2000)|
|--disable-admin-api | Disable the admin API, enabled by default (more info: https://mockoon.com/docs/latest/admin-api/overview/)|
|--disable-tls | Disable TLS for all environments. TLS configuration is part of the environment configuration (more info: https://mockoon.com/docs/latest/server-configuration/serving-over-tls/)|
|--max-transaction-logs | Maximum number of transaction logs to keep in memory for retrieval via the admin API (default: 100)|
|--enable-random-latency | Randomize global and responses latencies between 0 and the specified value (default: false)|
|--proxy | Override the environment's proxy settings (options: 'enabled' or 'disabled')|
|--public-base-url | Public base URL used to resolve [relative callback URLs](https://mockoon.com/docs/latest/callbacks/overview/#configure-a-callback) and for the [`baseUrl` templating helper](https://mockoon.com/docs/latest/templating/mockoon-request-helpers/#baseurl) (e.g. https://api.example.com or http://localhost:3000). Must include the protocol and port if non-standard.|
|-k, --token | Access token used to fetch cloud-hosted Mockoon environments (see  [access token documentation](https://mockoon.com/cloud/docs/access-tokens/))|
|-h, --help | Show CLI help|

**Examples**:

```bash
$ mockoon-cli start --data ~/data.json
$ mockoon-cli start --data ~/data.json --watch
$ mockoon-cli start --data ~/data1.json ~/data2.json --port 3000 3001 --hostname 127.0.0.1 192.168.1.1
$ mockoon-cli start --data https://file-server/data.json
$ mockoon-cli start --data ~/data.json --log-transaction
$ mockoon-cli start --data ~/data.json --disable-routes route1 route2 folder1
$ mockoon-cli start --data ~/data.json --disable-routes=*
$ mockoon-cli start --data ~/data.json --disable-routes "*"
$ mockoon-cli start --data ~/data.json --public-base-url https://api.example.com
$ mockoon-cli start --data cloud://def01727-aeb7-4cf1-9172-e0c38f22b224 --token mkn_sk_1234567890abcdef
```

#### Admin API

Each running mock API has an admin API enabled by default and available at `/mockoon-admin/`. This API allows you to interact with the running mock API, retrieve logs, and more. You can disable the admin API with the `--disable-admin-api` flag.

> 💡 To learn more about the admin API, check the [documentation](https://mockoon.com/docs/latest/admin-api/overview/).

#### Faker.js options

- **Locale**: You can set up Faker.js locale with the `--faker-locale` flag. If not provided, Faker.js will use the default locale: `en`. For a list of currently supported locales, you can check the [supported locales list](https://github.com/mockoon/mockoon/blob/main/packages/commons/src/models/faker.model.ts#L1) in Mockoon's commons library. You can also check [Faker.js locales list](https://fakerjs.dev/guide/localization.html#available-locales) for more information (⚠️ Some locales may not yet be implemented in Mockoon).
- **Seed**: You can set up Faker.js seed with the `--faker-seed` flag. If not provided, Faker.js will not use a seed. By providing a seed value, you can generate repeatable sequences of fake data. Using seeding will not always generate the same value but rather a predictable sequence.

#### Customize the environment variables prefix

You can access environment variables in your routes' responses by using the [`{{getEnvVar 'VARIABLE_NAME'}}` templating helper](https://mockoon.com/docs/latest/variables/environment-variables/). By default, only the environment variables prefixed with `MOCKOON_` are available, for example, `MOCKOON_MY_VARIABLE`.

You can customize the prefix with the `--env-vars-prefix` flag. For example, if you set `--env-vars-prefix CUSTOM_PREFIX_`, you will be able to access the environment variable `CUSTOM_PREFIX_MY_VARIABLE` in your routes' responses. To disable the prefix, set it to an empty string: `--env-vars-prefix ''` or `--env-vars-prefix=`.

#### Disabling routes

You can disable routes at runtime by providing their UUIDs or a keyword present in the route's path (do not include a leading slash). You can also disable all the routes present in a folder (including subfolders) by adding a keyword present in a folder name.

This is the counterpart of the "Toggle route" feature in the desktop application (right-click on a route -> "Toggle route").

For example, to disable all routes in a folder named `folder1`, and all routes having "users" in their paths, you can use `--disable-routes folder1 users`.

To disable all routes, use `--disable-routes=*` or `--disable-routes "*"`.

### `dockerize` command

Generates a Dockerfile used to build a self-contained image of one or more mock API. After building the image, no additional parameters will be needed when running the container.
This command takes similar flags as the [`start` command](#mockoon-start).
The `--disable-log-to-file` flag will be enabled by default in the resulting Dockerfile.

Please note that this command will copy your Mockoon environments files you provide with the `--data` flag and put them side by side with the generated Dockerfile.

For more information on how to build the image: [Using the dockerize command](#using-the-dockerize-command)

**Usage**:
`$ mockoon-cli dockerize`

**Options**:
|Flag|Description|
|-|-|
|-d, --data | [required] Path or URL to your Mockoon file|
|-p, --port | [required] Ports to expose in the Docker container. It should match the number of environment data files you provide with the --data flag.|
|-o, --output | [required] Generated Dockerfile path and name (e.g. `./folder/Dockerfile`)|
|-t, --log-transaction | Log the full HTTP transaction (request and response)|
|-h, --help | Show CLI help|

**Examples**:

```bash
$ mockoon-cli dockerize --data ~/data.json --output ./Dockerfile
$ mockoon-cli dockerize --data ~/data1.json ~/data2.json --output ./Dockerfile
$ mockoon-cli dockerize --data https://file-server/data.json --output ./Dockerfile
```

### `import` command

Import a Swagger v2/OpenAPI v3 specification file (YAML or JSON).

The output file will not be prettified by default. You can prettify it using the `--prettify` flag described below.

Note: This command is similar to the app's import feature, but it will not import directly to your desktop app. If you need to import and open in your desktop app, use the app's import feature instead.

**Usage**:
`$ mockoon-cli import`

**Options**:
|Flag|Description|
|-|-|
|-i, --input [required] |Path or URL to your Swagger v2/OpenAPI v3 file|
|-o, --output [required] |Generated Mockoon path and name (e.g. `./environment.json`)|
|-p, --prettify |Prettify output|
|-h, --help |Show CLI help|

**Examples**:

```bash
$ mockoon-cli import --input ~/input.json --output ./output.json
$ mockoon-cli import --input ~/input.yaml --output ./output.json
$ mockoon-cli import --input ~/input.json --output ./output.json --prettify
```

### `export` command

Export a mock API to an OpenAPI v3 specification file (JSON or YAML).

The output file will not be prettified by default for JSON. You can prettify it using the `--prettify` flag described below.

**Usage**:
`$ mockoon-cli export`

**Options**:
|Flag|Description|
|-|-|
|-i, --input [required] |Path or URL to your Mockoon data file|
|-o, --output [required] |Generated OpenApi v3 path and name (e.g. `./output.json`)|
|-f, --format |Output format, "json" or "yaml" (default: "json")|
|-p, --prettify |Prettify output (JSON only)|
|-h, --help |Show CLI help|

**Examples**:

```bash
$ mockoon-cli export --input ~/input.json --output ./output.json
$ mockoon-cli export --input ~/input.json --output ./output.json --prettify
$ mockoon-cli export --input ~/input.json --output ./output.yaml --format yaml
```

### `validate` command

Validate a Mockoon [environment JSON file](https://mockoon.com/docs/latest/mockoon-data-files/data-files-location/#data-files-schema) against the schema:

```sh-session
$ mockoon-cli validate --data ~/data1.json ~/data2.json
$ mockoon-cli validate --data https://file-server/data.json
```

> 💡 The `--data` flag behaves like the `--data` flag in the `start` command, meaning you can provide multiple paths or URLs to validate multiple files at once.

If the files are valid, you will see:

```
✓ Valid environment: ~/data1.json
✓ Valid environment: ~/data2.json
✓ All environments are valid
```

If one or more files are invalid, you will see validation errors:

```
Invalid environment: ~/data1.json
- "name" is required
- "port" must be a number
Invalid environment: ~/data2.json
- "routes" must be an array
 »   Error: Environments validation failed
```

> ⚠️ This command does not validate the OpenAPI specification files. OpenAPI files are validated by the [start command](#start-command) when you run it with an OpenAPI file as the `--data` parameter.

### `help` command

Returns information about a command.

**Usage**:
`$ mockoon-cli help [COMMAND]`

**Arguments and options**:
|Flag|Description|
|-|-|
|COMMAND |command to show help for|
|--all |see all commands in CLI|

## Use the GitHub Action

We maintain a [GitHub Action](https://github.com/marketplace/actions/mockoon-cli) that allows you to run your Mockoon CLI in your CI/CD pipelines.

You can find a [sample workflow](https://github.com/marketplace/actions/mockoon-cli#github-action-usage) in the GitHub Action's documentation.

Here is an example of a workflow that will run your mock API on every push to the `main` branch:

```yaml
name: Mockoon CLI demo

on:
  push:
    branches:
      - main

jobs:
  mockoon-cli-demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Mockoon CLI
        uses: mockoon/cli-action@v2
        with:
          # Mockoon CLI version, default to 'latest'
          version: 'latest'
          # Mockoon local data file or URL
          data-file: './mockoon-data.json'
          # port, default to 3000
          port: 3000
      - name: Make test call
        run: curl -X GET http://localhost:3000/endpoint`
```

> 💡 If you are building your own actions with the CLI, do not forget to add an `&` at the end of the command to run it in the background and avoid blocking the workflow: `mockoon-cli start -d ./data-file.json &`.

## Docker image

### Using the generic Docker image

A generic Docker image is published on the [Docker Hub Mockoon CLI repository](https://hub.docker.com/r/mockoon/cli). It uses `node:26-alpine` and installs the latest version of Mockoon CLI.

All of `mockoon-cli start` flags (`--port`, etc.) must be provided when running the container.

To load the Mockoon data, you can either mount a local data file and pass `mockoon-cli start` flags at the end of the command:

`docker run -d --mount type=bind,source=/home/your-data-file.json,target=/home/mockoon/data/your-data-file.json,readonly -p 3000:3000 mockoon/cli:latest --data /home/mockoon/data/your-data-file.json --port 3000`

Or directly pass a URL to the `mockoon-cli start` command, without mounting a local data file:

`docker run -d -p 3000:3000 mockoon/cli:latest -d https://raw.githubusercontent.com/mockoon/mock-samples/main/samples/generate-mock-data.json --port 3000`

Mockoon CLI's logs will be sent to stdout/stderr (console). File logging is disabled by default in the Docker image.

#### Docker compose

You can also use `docker-compose` with a `docker-compose.yml` file:

```
mock-server:
  image: mockoon/cli:latest
  command: ["--data", "/home/mockoon/data/your-data-file.json", "--port", "3000"]
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:3000/your-healthcheck-route || exit 1"]
    interval: 30s
    timeout: 5s
    retries: 2
    start_period: 10s
  volumes:
    - /home/your-data-file.json:/home/mockoon/data/your-data-file.json:readonly
```

> Please note that our [Docker image includes an `ENTRYPOINT`](https://github.com/mockoon/mockoon/blob/main/packages/cli/docker/Dockerfile#L16) that you may override or not. If you don't override it, and use Docker compose `command`, do not include `mockoon-cli start` as it is already included in the `ENTRYPOINT`.

This snippet also provides an optional healthcheck, which means you can block until the server is able to handle responses when bring it up by running `docker compose up --detach --wait`.

> This example requires a `your-healthcheck-route` route configured to return a 200 status code without latency.

### Using the `dockerize` command

You can use the [`dockerize` command](#mockoon-cli-dockerize) to generate a new Dockerfile that will allow you to build a self-contained image. Thus, no Mockoon CLI specific parameters will be needed when running the container.

- Run the `dockerize` command:

  `mockoon-cli dockerize --data ./sample-data.json --port 3000 --output ./tmp/Dockerfile`

- navigate to the `tmp` folder, where the Dockerfile has been generated and the environment file(s) copied:

  `cd tmp`

- Build the image:

  `docker build -t mockoon-image .`

- Run the container:

  `docker run -d -p <host_port>:3000 mockoon-image`

## Logs

Logs are located in `~/.mockoon-cli/logs/{mock-name}.log`. This file contains all the log entries (all levels) produced by the running mock server. Most of the errors occurring in Mockoon CLI (or the main application) are not critical and therefore considered as normal output. As an example, if the JSON body from an entering request is erroneous, Mockoon will log a JSON parsing error, but it won't block the normal execution of the application.

As the CLI is running in the foreground, logs are also sent to stdout (console).

### Transaction logging

When using the `--log-transaction` flag, logs will contain the full transaction (request and response) with the same information you can see in the desktop application "Logs" tab.

Example:

```json
{
  "app": "mockoon-server",
  "level": "info",
  "message": "Transaction recorded",
  "timestamp": "YYYY-MM-DDTHH:mm:ss.sssZ",
  "environmentName": "Demo API",
  "environmentUUID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "requestMethod": "GET",
  "requestPath": "/test",
  "requestProxied": false,
  "responseStatus": 200,
  "transaction": {
    "proxied": false,
    "request": {
      "body": "{}",
      "headers": [{ "key": "accept", "value": "*/*" }],
      "method": "GET",
      "params": [],
      "query": "",
      "queryParams": {},
      "route": "/test",
      "urlPath": "/test"
    },
    "response": {
      "body": "{}",
      "headers": [
        { "key": "content-type", "value": "application/json; charset=utf-8" }
      ],
      "statusCode": 200,
      "statusMessage": "OK"
    },
    "routeResponseUUID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "routeUUID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

The `transaction` model can be found [here](https://github.com/mockoon/mockoon/blob/main/packages/commons/src/models/server.model.ts#L27-L47).

### Disable logging

You can disable the logging to the console by redirecting the stdout and stderr outputs:

- Unix:

  ```sh-sessions
  mockoon-cli start --data ./data.json > /dev/null 2>&1
  ```

  or:

  ```sh-sessions
  mockoon-cli start --data ./data.json &> /dev/null
  ```

- Windows (cmd):

  ```sh-sessions
  mockoon-cli start --data ./data.json 2> NUL
  ```

  or:

  ```sh-sessions
  mockoon-cli start --data ./data.json > NUL 2>&1
  ```

- Windows (PowerShell):

  ```sh-sessions
  mockoon-cli start --data ./data.json 2> $null
  ```

  or:

  ```sh-sessions
  mockoon-cli start --data ./data.json > $null 2>&1
  ```

- Cross platform: use `dev-null-cli` package
  ```sh-sessions
  mockoon-cli start --data ./data.json | npx dev-null
  ```

You can also disable file logging by using th `--disable-log-to-file` flag. This is enabled by default in the Docker image.

## Mockoon's documentation

You will find Mockoon's [documentation](https://mockoon.com/docs/latest/about/) on the official website.

## Support us!

Mockoon is proudly **independent** and **open-source**, maintained without external funding. We rely on both **sponsorships** and **Mockoon Cloud subscriptions** to keep improving the project and building new features. A **big thank you** to the companies below for supporting our work and helping us grow (and all the [sponsors](https://github.com/mockoon/mockoon/blob/main/backers.md) who helped this project over time!):

### Platinum

<div align="center" style="margin-top:20px;margin-bottom:20px;">
  <a href="https://github.blog/2023-04-12-github-accelerator-our-first-cohort-and-whats-next/">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/github.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/github.png">
      <img src="https://mockoon.com/images/sponsors/light/github.png" alt="GitHub logo" />
      </picture>
  </a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://localazy.com/register?ref=a9CiDC61gOac-azO">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/localazy.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/localazy.png">
      <img src="https://mockoon.com/images/sponsors/light/localazy.png" alt="Localazy logo" />
      </picture>
  </a><br/><br/>
  <a href="https://serpapi.com/?utm_source=mockoon">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/serpapi.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/serpapi.png">
      <img src="https://mockoon.com/images/sponsors/light/serpapi.png" alt="SerpApi logo" />
      </picture>
  </a>
</div>

### Gold

<div align="center" style="margin-top:20px;margin-bottom:20px;">
  <a href="https://9proxy.com/?utm_source=Github&utm_campaign=mockoon">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/9proxy.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/9proxy.png">
      <img src="https://mockoon.com/images/sponsors/light/9proxy.png" alt="9proxy logo" />
      </picture>
  </a><br/><br/>
  <a href="https://coderabbit.link/mockoon">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/coderabbit.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/coderabbit.png">
      <img src="https://mockoon.com/images/sponsors/light/coderabbit.png" alt="CodeRabbit logo" />
      </picture>
  </a><br/><br/>
  <a href="https://www.rapidproxy.io/?ref=mockoon">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/rapidproxy.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/rapidproxy.png">
      <img src="https://mockoon.com/images/sponsors/light/rapidproxy.png" alt="Rapidproxy logo" />
      </picture>
  </a><br/><br/>
  <a href="https://talordata.com/?campaignid=rGAerPX1XrVAODD0&utm_source=mockoon&utm_term=mockoon">
      <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://mockoon.com/images/sponsors/light/talordata.png">
      <source media="(prefers-color-scheme: light)" srcset="https://mockoon.com/images/sponsors/talordata.png">
      <img src="https://mockoon.com/images/sponsors/light/talordata.png" alt="TalorData logo" />
      </picture>
  </a>
</div>

### Silver

<div align="center" style="margin-top:20px;margin-bottom:20px;">  
  <a href="https://www.emqx.io/">  
      <img src="https://mockoon.com/images/sponsors/emqx.png" alt="emqx logo" />
  </a>
</div>

If you'd like to **support Mockoon** as well, you can **become a sponsor** or **subscribe to Mockoon Cloud**, every contribution helps keep the project alive and evolving. Thank you!

<div align="center" style="margin-top:20px;margin-bottom:20px;">
<a href="https://github.com/sponsors/mockoon"><img src="https://mockoon.com/images/sponsor-btn.png?" width="250" alt="sponsor button" /></a>
</div>

## Subscribe to Mockoon Cloud

With advanced features for solo developers and teams, Mockoon Cloud supercharges your API development:

- ☁️ [cloud deployments](https://mockoon.com/cloud/docs/api-mock-cloud-deployments/)
- 🔄️ [data synchronization and real-time collaboration](https://mockoon.com/cloud/docs/data-synchronization-team-collaboration/)
- 🤖 [AI powered API mocking](https://mockoon.com/ai-powered-api-mocking/)
- 📃 Access to dozens of [ready-to-use JSON templates](https://mockoon.com/templates/).
- 💬 Priority support and training.

Upgrade today and take your API development to the next level.

<div align="center" style="margin-top:20px;margin-bottom:20px;">
<a href="https://mockoon.com/cloud/"><img src="https://mockoon.com/images/cloud-btn.png?" width="250" alt="cloud button" /></a>
</div>

## Support/feedback

You can discuss all things related to Mockoon's CLI, and ask for help, on the [official community](https://github.com/mockoon/mockoon/discussions). It's also a good place to discuss bugs and feature requests before opening an issue on this repository.

## Contributing

If you are interested in contributing to Mockoon, please take a look at the [contributing guidelines](https://github.com/mockoon/mockoon/blob/main/CONTRIBUTING.md).

Please also take a look at our [Code of Conduct](https://github.com/mockoon/.github/blob/main/CODE_OF_CONDUCT.md).

## Roadmap

If you want to know what will be coming in the next release you can check the global [Roadmap](https://mockoon.com/public-roadmap/) or [subscribe to our newsletter](https://mockoon.com/newsletter/).

```

### packages/cli/src/commands/start.ts
```
import {
  Environment,
  FakerAvailableLocales,
  FakerAvailableLocalesList,
  ServerErrorCodes,
  ServerOptions,
  defaultEnvironmentVariablesPrefix,
  defaultMaxCallbackDepth,
  defaultMaxTransactionLogs
} from '@mockoon/commons';
import {
  MockoonServer,
  ServerMessages,
  createLoggerInstance,
  listenServerEvents
} from '@mockoon/commons-server';
import { Command, Flags } from '@oclif/core';
import { watch } from 'chokidar';
import { join, resolve } from 'path';
import { format } from 'util';
import { Config } from '../config';
import {
  commonFlags,
  logTransactionFlag
} from '../constants/command.constants';
import { parseDataFile } from '../libs/data';
import { getDirname, transformEnvironmentName } from '../libs/utils';

export default class Start extends Command {
  public static override description = 'Start one or more mock API';

  public static override examples = [
    '$ mockoon-cli start --data ~/data.json',
    '$ mockoon-cli start --data ~/data.json --watch',
    '$ mockoon-cli start --data ~/data1.json ~/data2.json --port 3000 3001 --hostname 127.0.0.1 192.168.1.1',
    '$ mockoon-cli start --data https://file-server/data.json',
    '$ mockoon-cli start --data ~/data.json --log-transaction',
    '$ mockoon-cli start --data ~/data.json --disable-routes route1 route2',
    '$ mockoon-cli start --data ~/data.json --enable-random-latency'
  ];

  public static override flags = {
    ...commonFlags,
    ...logTransactionFlag,
    hostname: Flags.string({
      char: 'l',
      description: 'Listening hostname(s)',
      multiple: true,
      default: []
    }),
    port: Flags.integer({
      char: 'p',
      description: 'Override environment(s) port(s)',
      multiple: true,
      default: []
    }),
    'public-base-url': Flags.string({
      description:
        'Public base URL used to resolve relative callback URLs and for the baseUrl templating helper (e.g. https://api.example.com or http://localhost:3000). Must include the protocol and port if non-standard.',
      multiple: true,
      default: []
    }),
    repair: Flags.boolean({
      char: 'r',
      description:
        'If the data file seems too old, or an invalid Mockoon file, migrate/repair without prompting',
      default: false
    }),
    'disable-log-to-file': Flags.boolean({
      char: 'X',
      description: 'Only log to stdout and stderr',
      default: false
    }),
    'disable-routes': Flags.string({
      char: 'e',
      description:
        "Disable route(s) by UUID or keyword present in the route's path or keyword present in a folder name (do not include a leading slash)",
      multiple: true,
      default: []
    }),
    'faker-locale': Flags.string({
      char: 'c',
      description:
        "Faker locale (e.g. 'en', 'en_GB', etc. For supported locales, see documentation: https://github.com/mockoon/mockoon/blob/main/packages/cli/README.md#fakerjs-options)",
      default: 'en'
    }),
    'faker-seed': Flags.integer({
      char: 's',
      description: 'Number for the Faker.js seed (e.g. 1234)',
      default: undefined
    }),
    'env-vars-prefix': Flags.string({
      char: 'x',
      description: `Prefix of environment variables available at runtime (default: "${defaultEnvironmentVariablesPrefix}")`,
      multiple: false,
      default: defaultEnvironmentVariablesPrefix
    }),
    'disable-admin-api': Flags.boolean({
      description:
        'Disable the admin API, enabled by default (more info: https://mockoon.com/docs/latest/admin-api/overview/)',
      default: false
    }),
    'disable-tls': Flags.boolean({
      description:
        'Disable TLS for all environments. TLS configuration is part of the environment configuration (more info: https://mockoon.com/docs/latest/server-configuration/serving-over-tls/).',
      default: false
    }),
    'max-transaction-logs': Flags.integer({
      description: `Maximum number of transaction logs to keep in memory for retrieval via the admin API (default: ${defaultMaxTransactionLogs}).`,
      default: defaultMaxTransactionLogs
    }),
    'enable-random-latency': Flags.boolean({
      description:
        'Enable random latency from 0 to value specified in the route settings',
      default: false
    }),
    'enable-route-metadata-headers': Flags.boolean({
      description:
        'Add route metadata headers to responses (UUID and response metadata)',
      default: false
    }),
    proxy: Flags.string({
      description: "Override the environment's proxy settings",
      options: ['enabled', 'disabled'] as const
    }),
    watch: Flags.boolean({
      char: 'w',
      description:
        'Watch local data file(s) for changes and restart the server when a change is detected',
      default: false
    }),
    'polling-interval': Flags.integer({
      description: 'Local files watch polling interval in milliseconds',
      default: 2000
    }),
    token: Flags.string({
      char: 'k',
      description: 'Mockoon cloud access token',
      env: 'MOCKOON_CLOUD_TOKEN'
    }),
    'max-callback-depth': Flags.integer({
      description: `Maximum call stack depth for route responses with callback functions (default: ${defaultMaxCallbackDepth})`,
      default: defaultMaxCallbackDepth
    })
  };

  public async run(): Promise<void> {
    const { flags: userFlags } = await this.parse(Start);

    // validate flags
    if (
      !FakerAvailableLocalesList.includes(
        userFlags['faker-locale'] as FakerAvailableLocales
      )
    ) {
      this.error(
        'Invalid Faker.js locale. See documentation for supported locales (https://github.com/mockoon/mockoon/blob/main/packages/cli/README.md#fakerjs-options).'
      );
    }
    if (
      userFlags.data.some(
        (dataFilePath) =>
          dataFilePath.startsWith(Config.cloudScheme) && !userFlags.token
      )
    ) {
      this.error(
        'A token is required to load cloud environments. Use the --token flag or set the MOCKOON_CLOUD_TOKEN environment variable.'
      );
    }

    try {
      for (const [index, dataFilePath] of userFlags.data.entries()) {
        const parsedEnvironment = await parseDataFile(
          dataFilePath,
          {
            port: userFlags.port[index],
            hostname: userFlags.hostname[index],
            proxy: userFlags.proxy as 'enabled' | 'disabled'
          },
          userFlags.repair,
          userFlags.token
        );
        const server = this.createServer({
          environment: parsedEnvironment.environment,
          // resolve the environment path to an absolute path to avoid false positives when detecting path traversal
          environmentDirectory:
            getDirname(resolve(parsedEnvironment.originalPath)) ?? '',
          logTransaction: userFlags['log-transaction'],
          fileTransportOptions: userFlags['disable-log-to-file']
            ? null
            : {
                filename: join(
                  Config.logsPath,
                  `${transformEnvironmentName(
                    parsedEnvironment.environment.name
                  )}.log`
                )
              },
          disabledRoutes: userFlags['disable-routes'],
          fakerOptions: {
            locale: userFlags['faker-locale'] as FakerAvailableLocales,
            seed: userFlags['faker-seed']
          },
          envVarsPrefix: userFlags['env-vars-prefix'],
          enableAdminApi: !userFlags['disable-admin-api'],
          disableTls: userFlags['disable-tls'],
          maxTransactionLogs: userFlags['max-transaction-logs'],
          enableRandomLatency: userFlags['enable-random-latency'],
          enableRouteMetadataHeaders:
            userFlags['enable-route-metadata-headers'],
          maxCallbackDepth: userFlags['max-callback-depth'],
          publicBaseUrl: userFlags['public-base-url'][index]
        });

        if (!dataFilePath.startsWith('http') && userFlags.watch) {
          const watcher = watch(dataFilePath, {
            ignoreInitial: true,
            persistent: false,
            usePolling: true,
            interval: userFlags['polling-interval']
          });

          watcher.on('change', async (changedFilePath) => {
            try {
              const parsedNewEnvironment = await parseDataFile(
                changedFilePath,
                {
                  port: userFlags.port[index],
                  hostname: userFlags.hostname[index],
                  proxy: userFlags.proxy as 'enabled' | 'disabled'
                },
                userFlags.repair,
                userFlags.token
              );

              server.stop();

              server.updateEnvironment(parsedNewEnvironment.environment);
              server.start();
            } catch (error) {
              if (error instanceof Error) {
                this.error(
                  `Error while processing file change for ${changedFilePath}: ${error.message}`
                );
              }
            }
          });
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        this.error(error.message);
      }
    }
  }

  private createServer = (
    parameters: ServerOptions & {
      environment: Environment;
      logTransaction?: boolean;
      fileTransportOptions?: Parameters<typeof createLoggerInstance>[0] | null;
      publicBaseUrl?: string;
    }
  ) => {
    const logger = createLoggerInstance(parameters.fileTransportOptions);
    const server = new MockoonServer(parameters.environment, {
      environmentDirectory: parameters.environmentDirectory,
      disabledRoutes: parameters.disabledRoutes,
      fakerOptions: parameters.fakerOptions,
      envVarsPrefix: parameters.envVarsPrefix,
      enableAdminApi: parameters.enableAdminApi,
      disableTls: parameters.disableTls,
      maxTransactionLogs: parameters.maxTransactionLogs,
      enableRandomLatency: parameters.enableRandomLatency,
      enableRouteMetadataHeaders: parameters.enableRouteMetadataHeaders,
      maxCallbackDepth: parameters.maxCallbackDepth,
      publicBaseUrl: parameters.publicBaseUrl
    });

    listenServerEvents(
      server,
      parameters.environment,
      logger,
      parameters.logTransaction
    );

    server.on('error', (errorCode, originalError) => {
      const exitErrors = [
        ServerErrorCodes.PORT_ALREADY_USED,
        ServerErrorCodes.PORT_INVALID,
        ServerErrorCodes.HOSTNAME_UNAVAILABLE,
        ServerErrorCodes.HOSTNAME_UNKNOWN,
        ServerErrorCodes.CERT_FILE_NOT_FOUND,
        ServerErrorCodes.UNKNOWN_SERVER_ERROR
      ];

      let errorMessage: string | undefined = originalError?.message;

      switch (errorCode) {
        case ServerErrorCodes.PORT_ALREADY_USED:
        case ServerErrorCodes.PORT_INVALID:
          errorMessage = format(
            ServerMessages[errorCode],
            parameters.environment.port
          );
          break;
        case ServerErrorCodes.UNKNOWN_SERVER_ERROR:
          errorMessage = format(
            ServerMessages[errorCode],
            originalError?.message
          );
          break;
        case ServerErrorCodes.CERT_FILE_NOT_FOUND:
          errorMessage = ServerMessages[errorCode];
          break;
        case ServerErrorCodes.HOSTNAME_UNAVAILABLE:
        case ServerErrorCodes.HOSTNAME_UNKNOWN:
          errorMessage = format(
            ServerMessages[errorCode],
            parameters.environment.hostname
          );
          break;
      }

      // Cannot use this.error() as Oclif does not catch it (it seems to be lost due to the async nature of Node.js http server.listen errors).
      if (exitErrors.includes(errorCode)) {
        // red "»" character
        this.log(`\x1b[31m»\x1b[0m   Error: ${errorMessage}`);
        process.exit(2);
      }
    });

    process.on('SIGINT', () => {
      server.stop();
    });

    server.start();

    return server;
  };
}

```

### packages/commons-server/src/constants/server-messages.constants.ts
```
export const ServerMessages = {
  PORT_ALREADY_USED: 'Port %d is already in use',
  PORT_INVALID: 'Port %d is invalid or access is denied',
  INVALID_ROUTE_PATH: 'Invalid route path: %s',
  HOSTNAME_UNKNOWN: 'Unknown hostname/address provided: %s',
  HOSTNAME_UNAVAILABLE: 'Provided hostname/address is not available: %s',
  REQUEST_BODY_PARSE:
    'Error while trying to parse request body with compatible Content-Type (JSON, XML, form-data): %s',
  ROUTE_SERVING_ERROR: 'Error while serving the content: %s',
  ROUTE_FILE_SERVING_ERROR: 'Error while serving the file content: %s',
  PROXY_ERROR: 'An error occurred while trying to proxy to %s',
  UNKNOWN_SERVER_ERROR: 'An unknown server error occurred: %s',
  CERT_FILE_NOT_FOUND: 'Certificate file not found',
  ROUTE_NO_LONGER_EXISTS: 'This route no longer exists',
  HEADER_PARSING_ERROR: 'Header parsing error: %s',
  HEADER_PARSING_ERROR_LIGHT:
    '-- Header parsing error, see logs for more details --',
  SERVER_STARTED: 'Server started on port %d',
  SERVER_STOPPED: 'Server stopped',
  CALLBACK_FILE_ERROR: 'Error while attaching file to callback request: %s',
  CALLBACK_ERROR: 'Error while executing callback: %s',
  WS_UNKNOWN_ROUTE: 'No matching route found for websocket: %s',
  WS_UNSUPPORTED_CONTENT: 'Unsupported content received from websocket: %s',
  WS_SERVING_ERROR: 'Web socket serving error: %s'
};

```

### packages/commons-server/src/libs/logger.ts
```
import {
  createLogger,
  format as logFormat,
  Logger,
  transports as logsTransports
} from 'winston';
import {
  ConsoleTransportInstance,
  FileTransportInstance,
  FileTransportOptions
} from 'winston/lib/winston/transports';

export const createLoggerInstance = (
  fileTransportOptions?: FileTransportOptions | null
): Logger => {
  const transportsInstances: (
    | FileTransportInstance
    | ConsoleTransportInstance
  )[] = [new logsTransports.Console({ handleExceptions: true })];

  if (fileTransportOptions) {
    transportsInstances.push(
      new logsTransports.File({
        ...fileTransportOptions,
        handleExceptions: true
      })
    );
  }

  return createLogger({
    level: 'info',
    format: logFormat.combine(logFormat.timestamp(), logFormat.json()),
    transports: transportsInstances,
    exitOnError: false
  });
};

```

### packages/commons-server/src/libs/server/admin-api.ts
```
import { Environment, EnvironmentSchema, Transaction } from '@mockoon/commons';
import { Express, Request, Response } from 'express';
import { MockoonServer } from './server';
import { Sse } from './sse';

/**
 * Creates the Admin API endpoints
 * Documentation: https://mockoon.com/docs/latest/admin-api/overview/ *
 */
export const createAdminEndpoint = (
  app: Express,
  serverInstance: MockoonServer,
  {
    statePurgeCallback,
    getGlobalVariables,
    setGlobalVariables,
    purgeGlobalVariables,
    getDataBucket,
    getDataBuckets,
    purgeDataBuckets,
    getLogs,
    purgeLogs,
    envVarsPrefix,
    updateEnvironment
  }: {
    statePurgeCallback: () => void;
    getGlobalVariables: (key: string) => any;
    setGlobalVariables: (key: string, value: any) => void;
    purgeGlobalVariables: () => void;
    getDataBucket: (nameOrId: string) => any;
    getDataBuckets: () => any;
    purgeDataBuckets: () => void;
    getLogs: () => Transaction[];
    purgeLogs: () => void;
    envVarsPrefix: string;
    updateEnvironment: (environment: Environment) => void;
  }
): void => {
  const replayableEvents: any[] = [];
  const adminApiPrefix = '/mockoon-admin';
  const events = new Sse({
    getInitialEvents: (request: Request) => {
      const maxLogs =
        typeof request.query['maxlogs'] === 'string'
          ? parseInt(request.query['maxlogs'], 10)
          : undefined;
      const logs = getLogs();
      const limitedLogs =
        maxLogs != null && !isNaN(maxLogs) && maxLogs > 0
          ? logs.slice(maxLogs * -1)
          : logs;

      return [
        ...replayableEvents,
        ...limitedLogs.map((transaction) => ({
          event: 'transaction-complete',
          transaction
        }))
      ];
    }
  });

  app.use(`${adminApiPrefix}*`, (req, res, next) => {
    res.setHeaders(
      new Headers({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods':
          'GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS',
        'Access-Control-Allow-Headers':
          'Content-Type, Origin, Accept, Authorization, Content-Length, X-Requested-With'
      })
    );
    next();
  });

  app.get(adminApiPrefix, (req, res) => {
    res.send({
      response:
        "Welcome to Mockoon's admin API. Check the documentation at https://mockoon.com/docs/latest/admin-api/overview/ for more information."
    });
  });

  serverInstance.on('stopped', () => {
    events.close();
  });

  // listen to server events and send them through the SSE
  serverInstance.on('transaction-complete', (transaction) => {
    const event = { event: 'transaction-complete', transaction };

    events.send(event);
  });

  serverInstance.on('data-bucket-processed', (dataBuckets) => {
    const event = { event: 'data-bucket-processed', dataBuckets };

    events.send(event);
    replayableEvents.push(event);
  });

  app.get(`${adminApiPrefix}/events`, events.requestListener);

  const stateEndpoint = `${adminApiPrefix}/state`;
  const purgeHandler = (req, res) => {
    statePurgeCallback();

    purgeDataBuckets();
    purgeGlobalVariables();
    purgeLogs();

    res.send({
      response: 'Server has been reset to its initial state'
    });
  };

  /**
   * Get the value of an environment variable
   *
   * @param req
   * @param res
   */
  const getEnvVarHandler = (req, res) => {
    // get var name from path
    let varName = req.params.key;

    if (!varName.startsWith(envVarsPrefix)) {
      varName = envVarsPrefix + varName;
    }

    if (varName) {
      // send var or 404
      if (process.env[varName] !== undefined) {
        res.send({
          key: varName,
          value: process.env[varName]
        });
      } else {
        res.status(404).send({ message: 'Environment variable not found' });
      }
    } else {
      res.status(400).send({ message: 'Invalid request' });
    }
  };

  /**
   * Set the value of an environment variable
   *
   * @param req
   * @param res
   */
  const setEnvVarHandler = (req, res) => {
    try {
      const { key, value } = req.body;
      if (key !== undefined && value !== undefined) {
        process.env[key] = value;

        res.send({
          message: `Environment variable '${key}' has been set to '${value}'`
        });
      } else {
        throw new Error('Key or value missing from request');
      }
    } catch (_error) {
      res.status(400).send({ message: 'Invalid request' });
    }
  };

  /**
   * Get the value of a global variable
   *
   * @param req
   * @param res
   */
  const getGlobalVarHandler = (req, res) => {
    // get var name from path
    const key = req.params.key;

    if (key) {
      // send var or 404
      if (getGlobalVariables(key) !== undefined) {
        res.send({
          key,
          value: getGlobalVariables(key)
        });
      } else {
        res.status(404).send({ message: 'Global variable not found' });
      }
    } else {
      res.status(400).send({ message: 'Invalid request' });
    }
  };

  /**
   * Set the value of a global variable
   *
   * @param req
   * @param res
   */
  const setGlobalVarHandler = (req, res) => {
    try {
      const { key, value } = req.body;
      if (key !== undefined && value !== undefined) {
        setGlobalVariables(key, value);
        res.send({
          message: `Global variable '${key}' has been set to '${value}'`
        });
      } else {
        throw new Error('Key or value missing from request');
      }
    } catch (_error) {
      res.status(400).send({ message: 'Invalid request' });
    }
  };

  /**
   * Trigger the purge of global variables, deleting all of them
   *
   * @param req
   * @param res
   */
  const purgeGlobalVarsHandler = (req, res) => {
    try {
      purgeGlobalVariables();
      res.send({
        message: 'Global variables have been purged'
      });
    } catch (_error) {
      res.status(500).send({ message: 'Failed to purge global variables' });
    }
  };

  /**
   * Get data buckets current states (without value)
   *
   * @param req
   * @param res
   */
  const getDataBucketsHandler = (req, res) => {
    const buckets = getDataBuckets();

    res.send(
      buckets.map((bucket) => ({
        id: bucket.id,
        name: bucket.name,
        parsed: bucket.parsed,
        validJson: bucket.validJson
      }))
    );
  };

  /**
   * Get a data bucket current parsed value
   *
   * @param req
   * @param res
   */
  const getDataBucketHandler = (req, res) => {
    const nameOrId = req.params.nameOrId;

    if (nameOrId) {
      const bucket = getDataBucket(nameOrId);

      if (bucket) {
        res.send(bucket);
      } else {
        res.status(404).send({ message: 'Data bucket not found' });
      }
    } else {
      res.status(400).send({ message: 'Invalid request' });
    }
  };

  /**
   * Trigger the purge of data buckets, resetting them to their initial state
   *
   * @param req
   * @param res
   */
  const purgeDataBucketsHandler = (req, res) => {
    try {
      purgeDataBuckets();
      res.send({
        message: 'Data buckets have been reset to their initial state'
      });
    } catch (_error) {
      res.status(500).send({ message: 'Failed to reset the data buckets' });
    }
  };

  /**
   * Return the transaction logs with pagination.
   * This is similar to the desktop app's Logs tab information.
   *
   * @param req
   * @param res
   */
  const getLogsHandler = (req: Request, res: Response) => {
    const page =
      typeof req.query['page'] === 'string'
        ? parseInt(req.query['page'], 10)
        : 1;
    const limit =
      typeof req.query['limit'] === 'string'
        ? parseInt(req.query['limit'], 10)
        : 10;
    const logs = getLogs();
    const start = (page - 1) * limit;

    res.send(logs.slice(start, start + limit));
  };

  /**
   * Trigger the purge of transaction logs, deleting all of them
   *
   * @param req
   * @param res
   */
  const purgeLogsHandler = (req, res) => {
    try {
      purgeLogs();
      res.send({
        message: 'Logs have been purged'
      });
    } catch (_error) {
      res.status(500).send({ message: 'Failed to purge logs' });
    }
  };

  // global state endpoints
  app.purge(stateEndpoint, purgeHandler);
  app.post(`${stateEndpoint}/purge`, purgeHandler);

  // Logs endpoints
  app.get(`${adminApiPrefix}/logs`, getLogsHandler);
  app.post(`${adminApiPrefix}/logs/purge`, purgeLogsHandler);
  app.purge(`${adminApiPrefix}/logs`, purgeLogsHandler);

  // env vars endpoints
  app.get(`${adminApiPrefix}/env-vars/:key`, getEnvVarHandler);
  app.post(`${adminApiPrefix}/env-vars`, setEnvVarHandler);
  app.put(`${adminApiPrefix}/env-vars`, setEnvVarHandler);
  app.patch(`${adminApiPrefix}/env-vars`, setEnvVarHandler);

  // global vars endpoints
  app.get(`${adminApiPrefix}/global-vars/:key`, getGlobalVarHandler);
  app.post(`${adminApiPrefix}/global-vars`, setGlobalVarHandler);
  app.put(`${adminApiPrefix}/global-vars`, setGlobalVarHandler);
  app.patch(`${adminApiPrefix}/global-vars`, setGlobalVarHandler);
  app.purge(`${adminApiPrefix}/global-vars`, purgeGlobalVarsHandler);
  app.post(`${adminApiPrefix}/global-vars/purge`, purgeGlobalVarsHandler);

  // data buckets endpoints
  app.get(`${adminApiPrefix}/data-buckets`, getDataBucketsHandler);
  app.get(`${adminApiPrefix}/data-buckets/:nameOrId`, getDataBucketHandler);
  app.purge(`${adminApiPrefix}/data-buckets`, purgeDataBucketsHandler);
  app.post(`${adminApiPrefix}/data-buckets/purge`, purgeDataBucketsHandler);

  /**
   * Update the environment
   *
   * Note: not everything can be updated during runtime, only:
   * - some environment properties (headers, proxy headers, latency, etc.)
   * - route responses (headers, latency, status code, etc.)
   * - some route properties (response mode)
   *
   * What cannot be updated:
   * - route paths and methods
   * - environment port, hostname, and proxy target
   * - adding or removing routes
   * - data buckets
   * - callbacks
   */
  app.put(`${adminApiPrefix}/environment`, (req, res) => {
    try {
      const environment: Environment = EnvironmentSchema.validate(
        req.body
      ).value;

      if (!environment) {
        res.status(400).send({ message: 'Invalid environment format' });

        return;
      }

      updateEnvironment(environment);

      res.send({
        message: 'Environment updated'
      });
    } catch (_error) {
      res.status(400).send({ message: 'Invalid environment format' });
    }
  });
};

```

### packages/commons-server/src/libs/server/events-listeners.ts
```
import {
  CloneObject,
  Environment,
  Header,
  InFlightRequest,
  InvokedCallback,
  Methods,
  Transaction
} from '@mockoon/commons';
import { format } from 'util';
import { Logger } from 'winston';
import { ServerMessages } from '../../constants/server-messages.constants';
import { MockoonServer } from './server';

const authorizationHeaders = ['authorization', 'proxy-authorization'];
const filterAuthorizationHeaders = (header: Header) => {
  if (authorizationHeaders.includes(header.key.toLowerCase())) {
    const headerSplit = header.value.split(' ');

    header.value = headerSplit.length === 1 ? '***' : `${headerSplit[0]} ***`;
  }

  return header;
};

export const listenServerEvents = function (
  server: MockoonServer,
  environment: Environment,
  logger: Logger,
  logTransaction?: boolean
): void {
  const defaultLogMeta: any = {
    environmentName: environment.name,
    environmentUUID: environment.uuid,
    app: 'mockoon-server'
  };

  server.on('started', () => {
    logger.info(format(ServerMessages.SERVER_STARTED, environment.port), {
      ...defaultLogMeta
    });

    if (process.send) {
      process.send('ready');
    }
  });

  server.on('stopped', () => {
    logger.info(ServerMessages.SERVER_STOPPED, { ...defaultLogMeta });
  });

  server.on('error', (errorCode, error, payload) => {
    const errorMeta = { ...defaultLogMeta };
    let message = '';

    switch (errorCode) {
      case 'PORT_ALREADY_USED':
        message = format(ServerMessages[errorCode], environment.port);
        break;
      case 'PORT_INVALID':
        message = format(ServerMessages[errorCode], environment.port);
        break;
      case 'HOSTNAME_UNKNOWN':
        message = format(ServerMessages[errorCode], environment.hostname);
        break;
      case 'HOSTNAME_UNAVAILABLE':
        message = format(ServerMessages[errorCode], environment.hostname);
        break;
      case 'REQUEST_BODY_PARSE':
      case 'ROUTE_SERVING_ERROR':
      case 'ROUTE_FILE_SERVING_ERROR':
      case 'UNKNOWN_SERVER_ERROR':
      case 'HEADER_PARSING_ERROR':
      case 'CALLBACK_ERROR':
      case 'CALLBACK_FILE_ERROR':
      case 'WS_SERVING_ERROR':
      case 'WS_UNKNOWN_ROUTE':
      case 'WS_UNSUPPORTED_CONTENT':
      case 'INVALID_ROUTE_PATH':
        message = format(ServerMessages[errorCode], error?.message || '');
        break;
      case 'CERT_FILE_NOT_FOUND':
        message = format(ServerMessages[errorCode]);
        break;
      case 'PROXY_ERROR':
        message = format(
          ServerMessages[errorCode],
          environment.proxyHost,
          error?.message
        );
        break;
      case 'ROUTE_NO_LONGER_EXISTS':
        message = ServerMessages[errorCode];
        break;
    }

    logger.error(message, { ...errorMeta, ...payload });
  });

  server.on('transaction-complete', (transaction: Transaction) => {
    const logMeta: { transaction: Transaction } = {
      ...defaultLogMeta,
      requestMethod: transaction.request.method.toUpperCase(),
      requestPath: transaction.request.urlPath,
      responseStatus: transaction.response.statusCode,
      requestProxied: transaction.proxied
    };

    if (logTransaction) {
      logMeta.transaction = CloneObject(transaction) as Transaction;
      logMeta.transaction.request.headers =
        logMeta.transaction.request.headers.map(filterAuthorizationHeaders);
      logMeta.transaction.response.headers =
        logMeta.transaction.response.headers.map(filterAuthorizationHeaders);
      logMeta.transaction.request.method =
        logMeta.transaction.request.method.toUpperCase() as Methods;
    }

    logger.info('Transaction recorded', logMeta);
  });

  server.on('callback-invoked', (callback: InvokedCallback) => {
    const logMeta: { callback: InvokedCallback } = {
      ...defaultLogMeta,
      callbackName: callback.name,
      callbackMethod: callback.method,
      callbackUrl: callback.url,
      callbackStatus: callback.status
    };

    if (logTransaction) {
      const clonedCallback = CloneObject(callback) as InvokedCallback;
      logMeta.callback = clonedCallback;
      logMeta.callback.requestHeaders = logMeta.callback.requestHeaders.map(
        filterAuthorizationHeaders
      );
      logMeta.callback.responseHeaders = logMeta.callback.responseHeaders.map(
        filterAuthorizationHeaders
      );
    }
    logger.info('Callback invoked', logMeta);
  });

  server.on('ws-new-connection', (inflightRequest: InFlightRequest) => {
    const logMeta: { inflightRequest: InFlightRequest } = {
      ...defaultLogMeta,
      websocketUuid: inflightRequest.uuid,
      url: inflightRequest.request.urlPath,
      routeUUID: inflightRequest.routeUUID
    };

    if (logTransaction) {
      logMeta.inflightRequest = CloneObject(inflightRequest) as InFlightRequest;
      logMeta.inflightRequest.request.headers = logMeta.inflightRequest.request
        ?.headers
        ? logMeta.inflightRequest.request?.headers.map(
            filterAuthorizationHeaders
          )
        : [];
    }
    logger.info('New WebSocket connection', logMeta);
  });

  server.on(
    'ws-message-received',
    (inflightRequest: InFlightRequest, message: string) => {
      const logMeta: { inflightRequest: InFlightRequest; messageData: string } =
        {
          ...defaultLogMeta,
          websocketUuid: inflightRequest.uuid,
          url: inflightRequest.request.urlPath,
          routeUUID: inflightRequest.routeUUID
        };

      if (logTransaction) {
        logMeta.inflightRequest = CloneObject(
          inflightRequest
        ) as InFlightRequest;
        logMeta.messageData = message;
        logMeta.inflightRequest.request.headers = logMeta.inflightRequest
          .request?.headers
          ? logMeta.inflightRequest.request?.headers.map(
              filterAuthorizationHeaders
            )
          : [];
      }
      logger.info('WebSocket message received', logMeta);
    }
  );

  server.on(
    'ws-closed',
    (request: InFlightRequest, code: number, reason?: string | null) => {
      const logMeta: { inflightRequest: InFlightRequest } = {
        ...defaultLogMeta,
        websocketUuid: request.uuid,
        code,
        reason
      };

      if (logTransaction) {
        logMeta.inflightRequest = CloneObject(request) as InFlightRequest;
        logMeta.inflightRequest.request.headers = logMeta.inflightRequest
          .request?.headers
          ? logMeta.inflightRequest.request?.headers.map(
              filterAuthorizationHeaders
            )
          : [];
      }

      logger.info('WebSocket closed', logMeta);
    }
  );
};

```

### packages/commons-server/src/libs/server/server.ts
```
import {
  BINARY_BODY,
  BodyTypes,
  CORSHeaders,
  Callback,
  Environment,
  FileExtensionsWithTemplating,
  GetContentType,
  GetRouteResponseContentType,
  Header,
  IsValidURL,
  MimeTypesWithTemplating,
  ParsedJSONBodyMimeTypes,
  ParsedXMLBodyMimeTypes,
  ProcessedDatabucket,
  Route,
  RouteResponse,
  RouteType,
  ServerErrorCodes,
  ServerEvents,
  ServerOptions,
  StreamingMode,
  Transaction,
  crudRoutesBuilder,
  dedupSlashes,
  defaultEnvironmentVariablesPrefix,
  defaultMaxCallbackDepth,
  defaultMaxTransactionLogs,
  deterministicStringify,
  generateUUID,
  getLatency,
  pathMatch,
  pathMatchErrorBuilder,
  preparePath,
  routesFromFolder,
  stringIncludesArrayItems
} from '@mockoon/commons';
import appendField from 'append-field';
import busboy from 'busboy';
import cookieParser from 'cookie-parser';
import { EventEmitter } from 'events';
import express, { Application, NextFunction, Request, Response } from 'express';
import { createReadStream, readFile, readFileSync, statSync } from 'fs';
import type { RequestListener } from 'http';
import { createServer as httpCreateServer, Server as httpServer } from 'http';
import { createProxyMiddleware } from 'http-proxy-middleware';
import {
  createServer as httpsCreateServer,
  Server as httpsServer
} from 'https';
import killable from 'killable';
import { AddressInfo, isIPv6 } from 'node:net';
import { basename, extname, isAbsolute, parse, relative, resolve } from 'path';
import { parse as qsParse } from 'qs';
import rangeParser from 'range-parser';
import { Readable } from 'stream';
import { SecureContextOptions } from 'tls';
import TypedEmitter from 'typed-emitter';
import { parse as parseUrl } from 'url';
import { format } from 'util';
import { WebSocket, WebSocketServer } from 'ws';
import { xml2js } from 'xml-js';
import { ServerMessages } from '../../constants/server-messages.constants';
import { DefaultTLSOptions } from '../../constants/ssl.constants';
import { SetFakerLocale, SetFakerSeed } from '../faker';
import { ServerRequest, fromExpressRequest, fromWsRequest } from '../requests';
import { ResponseRulesInterpreter } from '../response-rules-interpreter';
import { TemplateParser } from '../template-parser';
import {
  CreateCallbackInvocation,
  CreateInFlightRequest,
  CreateTransaction,
  isBodySupportingMethod,
  isValidStatusCode,
  mimeTypeLookup,
  resolvePathFromEnvironment
} from '../utils';
import { createAdminEndpoint } from './admin-api';
import { databucketActions } from './crud';
import {
  generateDatabuckets,
  generateRequestDatabuckets,
  regenerateDatabuckets
} from './data-buckets';
import {
  BroadcastContext,
  DelegatedBroadcastHandler,
  WebSocketServerInstance,
  getSafeStreamingInterval,
  isWebSocketOpen,
  messageToString,
  serveFileContentInWs
} from './ws';

/**
 * Create a server instance from an Environment object.
 *
 * Extends an EventEmitter.
 *
 * ⚠️ The function listenServerEvents must be used to listen to server events
 * and avoid the EventEmitter to throw errors due to the lack of listeners.
 *
 * Example:
 *
 * ```
 * const server = new MockoonServer(environment);
 * const logger = createLoggerInstance();
 * listenServerEvents(server, environment, logger, false);
 *
 * // or ate least listen to the error event
 * server.on('error', (errorCode, originalError) => {});
 * ```
 */
export class MockoonServer extends (EventEmitter as new () => TypedEmitter<ServerEvents>) {
  private serverInstance: httpServer | httpsServer;
  private webSocketServers: WebSocketServerInstance[] = [];
  private tlsOptions: SecureContextOptions = {};
  private processedDatabuckets: ProcessedDatabucket[] = [];
  // store the request number for each route
  private requestNumbers: Record<string, number> = {};
  // templating global variables
  private globalVariables: Record<string, any> = {};
  private options: ServerOptions = {
    environmentDirectory: '.',
    disabledRoutes: [],
    envVarsPrefix: defaultEnvironmentVariablesPrefix,
    enableAdminApi: true,
    disableTls: false,
    maxTransactionLogs: defaultMaxTransactionLogs,
    enableRandomLatency: false,
    enableRouteMetadataHeaders: false,
    maxFileUploads: 10,
    maxFileSize: 10 * 1024 * 1024, // 10MB
    maxCallbackDepth: defaultMaxCallbackDepth
  };
  private transactionLogs: Transaction[] = [];
  private effectiveRestRoutes: Route[] = [];
  private effectiveWebSocketRoutes: Route[] = [];

  constructor(
    private environment: Environment,
    options: Partial<ServerOptions> = {}
  ) {
    super();

    this.options = {
      ...this.options,
      ...options,
      envVarsPrefix: options.envVarsPrefix ?? defaultEnvironmentVariablesPrefix,
      maxCallbackDepth: options.maxCallbackDepth ?? defaultMaxCallbackDepth
    };

    this.computeEffectiveRestRoutes();
    this.computeEffectiveWebSocketRoutes();
  }

  /**
   * Start a server
   */
  public start(): void {
    const requestListener = this.createRequestListener();

    // create https or http server instance
    if (this.environment.tlsOptions.enabled && !this.options.disableTls) {
      try {
        this.tlsOptions = this.buildTLSOptions(this.environment);

        this.serverInstance = httpsCreateServer(this.tlsOptions);
      } catch (error: any) {
        if (error.code === 'ENOENT') {
          this.emit('error', ServerErrorCodes.CERT_FILE_NOT_FOUND, error);
        } else {
          this.emit('error', ServerErrorCodes.UNKNOWN_SERVER_ERROR, error);
        }
      }
    } else {
      this.serverInstance = httpCreateServer();
    }

    // make serverInstance killable
    this.serverInstance = killable(this.serverInstance);

    // set timeout long enough to allow long latencies
    this.serverInstance.setTimeout(3_600_000);

    // handle server errors
    this.serverInstance.on('error', (error: NodeJS.ErrnoException) => {
      let errorCode: ServerErrorCodes;

      switch (error.code) {
        case 'EADDRINUSE':
          errorCode = ServerErrorCodes.PORT_ALREADY_USED;
          break;
        case 'EACCES':
          errorCode = ServerErrorCodes.PORT_INVALID;
          break;
        case 'EADDRNOTAVAIL':
          errorCode = ServerErrorCodes.HOSTNAME_UNAVAILABLE;
          break;
        case 'ENOTFOUND':
          errorCode = ServerErrorCodes.HOSTNAME_UNKNOWN;
          break;
        default:
          errorCode = ServerErrorCodes.UNKNOWN_SERVER_ERROR;
      }
      this.emit('error', errorCode, error);
    });

    this.serverInstance.on('request', requestListener);

    this.createWebsocketRoutes();

    try {
      this.serverInstance.listen(
        { port: this.environment.port, host: this.environment.hostname },
        () => {
          this.emit('started');
        }
      );
    } catch (error: any) {
      if (error.code === 'ERR_SOCKET_BAD_PORT') {
        this.emit('error', ServerErrorCodes.PORT_INVALID, error);
      }
    }
  }

  /**
   * Kill the server
   */
  public stop(): void {
    this.closeWsServers();

    if (this.serverInstance) {
      this.serverInstance.kill(() => {
        this.emit('stopped');
      });
    }
  }

  /**
   * Create a request listener
   */
  public createRequestListener(): RequestListener {
    /**
     * Apply faker.js settings at each server start.
     * Locale must be set before seed.
     * We do this in the request listener to allow changing the locale and seed from the serverless package too, which is not using the start/stop methods.
     */
    SetFakerLocale(this.options.fakerOptions?.locale ?? 'en');
    SetFakerSeed(this.options.fakerOptions?.seed ?? undefined);

    const app = express();
    app.disable('x-powered-by');
    app.disable('etag');

    app.use(this.removeExpectHeader);

    // This middleware is required to parse the body for createAdminEndpoint requests
    app.use(this.parseBody);

    if (this.options.enableAdminApi) {
      // admin endpoint must be created before all other routes to avoid conflicts
      createAdminEndpoint(app, this, {
        statePurgeCallback: () => {
          // reset request numbers
          Object.keys(this.requestNumbers).forEach((routeUUID) => {
            this.requestNumbers[routeUUID] = 1;
          });
        },
        getGlobalVariables: (key: string) => this.globalVariables[key],
        setGlobalVariables: (key: string, value: any) => {
          this.globalVariables[key] = value;
        },
        purgeGlobalVariables: () => {
          this.globalVariables = {};
        },
        getDataBucket: this.getProcessedDatabucket.bind(this),
        getDataBuckets: () => this.processedDatabuckets,
        purgeDataBuckets: () => {
          this.processedDatabuckets = [];
          generateDatabuckets(
            this.environment,
            this.processedDatabuckets,
            this.globalVariables,
            this.options,
            () => {
              this.emitProcessedDatabuckets();
            }
          );
        },
        getLogs: () => this.transactionLogs,
        purgeLogs: () => {
          this.transactionLogs = [];
        },
        envVarsPrefix: this.options.envVarsPrefix,
        updateEnvironment: (environment: Environment) => {
          this.updateEnvironment(environment);
        }
      });
    }

    // process databuckets after admin endpoint creation to properly catch the databucket processed event
    generateDatabuckets(
      this.environment,
      this.processedDatabuckets,
      this.globalVariables,
      this.options,
      () => {
        this.emitProcessedDatabuckets();
      }
    );

    app.use(this.emitEvent);
    app.use(this.delayResponse);
    app.use(this.deduplicateRequestSlashes);
    app.use(cookieParser());
    app.use(this.logRequest);
    app.use(this.setResponseHeaders);

    this.createRestRoutes(app);
    this.setCors(app);
    this.enableProxy(app);
    app.use(this.errorHandler);

    return app;
  }
  /**
   * Return a processed databucket by name, id, or uuid
   *
   * @param identifier
   */
  public getProcessedDatabucket(identifier: string) {
    return this.processedDatabuckets.find(
      (processedDatabucket) =>
        processedDatabucket.name.toLowerCase() === identifier.toLowerCase() ||
        processedDatabucket.id === identifier.toLowerCase() ||
        processedDatabucket.uuid === identifier.toLowerCase()
    );
  }

  /**
   * Method that can be used to update the server's environment and
   * the disabled routes.
   *
   * It will recompute the effective route list to be used later during
   * request handling.
   *
   * @param environment
   */
  public updateEnvironment(environment: Environment): void {
    const previousDataBuckets = this.environment.data;

    this.environment = environment;

    regenerateDatabuckets(
      previousDataBuckets,
      environment.data,
      this.processedDatabuckets,
      environment,
      this.globalVariables,
      this.options,
      () => {
        this.emitProcessedDatabuckets();
      }
    );

    this.computeEffectiveRestRoutes();
    this.regenerateWebSocketRoutes();
  }

  /**
   * Method to update the list of disabled routes without restarting the server.
   */
  public updateDisabledRoutes(disabledRoutes: string[]): void {
    this.options.disabledRoutes = disabledRoutes;

    this.computeEffectiveRestRoutes();
    this.regenerateWebSocketRoutes();
  }

  /**
   * ### Middleware ###
   * Remove the Expect: 100-continue header.
   * Express will always respond with 100 Continue if the header is present.
   *
   * However, http-proxy-middleware hang (onProxyReq is not triggered) if the header is present.
   * See https://github.com/http-party/node-http-proxy/issues/1219
   * A workaround would be to remove it and re-add it in the onProxyReq function,
   * but it's probably better to just remove it.
   *
   * @param request
   * @param response
   * @param next
   */
  private removeExpectHeader = (
    request: Request,
    response: Response,
    next: NextFunction
  ) => {
    const expectHeader = request.get('expect');

    if (expectHeader?.toLowerCase().includes('100-continue')) {
      delete request.headers.expect;
    }

    next();
  };

  /**
   * ### Middleware ###
   * Emit the SERVER_ENTERING_REQUEST event
   *
   * @param request
   * @param response
   * @param next
   */
  private emitEvent = (
    request: Request,
    response: Response,
    next: NextFunction
  ) => {
    this.emit('entering-request');
    next();
  };

  /**
   * ### Middleware ###
   * Add global latency to the mock server
   *
   * @param request
   * @param response
   * @param next
   */
  private delayResponse = (
    request: Request,
    response: Response,
    next: NextFunction
  ) => {
    setTimeout(
      next,
      getLatency(this.environment.latency, this.options.enableRandomLatency)
    );
  };

  /**
   * ### Middleware ###
   * Remove duplicate slashes in entering call paths
   *
   * @param request
   * @param response
   * @param next
   */
  private deduplicateRequestSlashes(
    request: Request,
    response: Response,
    next: NextFunction
  ) {
    request.url = dedupSlashes(request.url);

    next();
  }

  /**
   * Process the raw body and parse it if needed
   *
   * @param request
   * @param next
   * @param rawBody
   * @param requestContentType
   */
  private processRawBody(request, next, rawBody, requestContentType) {
    request.rawBody = Buffer.concat(rawBody);
    request.stringBody = request.rawBody.toString('utf8');

    try {
      if (requestContentType) {
        if (
          stringIncludesArrayItems(ParsedJSONBodyMimeTypes, requestContentType)
        ) {
          request.body = JSON.parse(request.stringBody);
          next();
        } else if (
          requestContentType.includes('application/x-www-form-urlencoded')
        ) {
          request.body = qsParse(request.stringBody, {
            depth: 10
          });
          next();
        } else if (requestContentType.includes('multipart/form-data')) {
          const busboyParse = busboy({
            headers: request.headers,
            limits: {
              fieldNameSize: 1000,
              files: this.options.maxFileUploads,
              fileSize: this.options.maxFileSize
            }
          });

          busboyParse.on('field', (name, value, info) => {
            if (request.body === undefined) {
              request.body = {};
            }

            if (name != null && !info.nameTruncated && !info.valueTruncated) {
              // add support for first level array fields (e.g. multiple fields with the same name without brackets)
              if (
                !name.includes('[') &&
                request.body[name] !== undefined &&
                !Array.isArray(request.body[name])
              ) {
                request.body[name] = [request.body[name]];
                name = `${name}[]`;
              }
              appendField(request.body, name, value);
            }
          });

          busboyParse.on(
            'file',
            (
              name: string,
              stream: Readable,
              info: { filename: string; encoding: string; mimeType: string }
            ) => {
              if (request.body === undefined) {
                request.body = {};
              }

              const file = {
                filename: info.filename,
                mimetype: info.mimeType,
                size: 0
              };

              stream.on('data', (data) => {
                file.size += data.length;
              });

              stream.on('close', () => {
                // add support for first level array fields (e.g. multiple fields with the same name without brackets)
                if (
                  !name.includes('[') &&
                  request.body[name] !== undefined &&
                  !Array.isArray(request.body[name])
                ) {
                  request.body[name] = [request.body[name]];
                  name = `${name}[]`;
                }

                appendField(request.body, name, file);
              });
            }
          );

          busboyParse.on('error', (error: any) => {
            this.emit('error', ServerErrorCodes.REQUEST_BODY_PARSE, error);
            // we want to continue answering the call despite the parsing errors
            next();
          });

          busboyParse.on('finish', () => {
            next();
          });

          busboyParse.end(request.rawBody);
        } else if (
          stringIncludesArrayItems(ParsedXMLBodyMimeTypes, requestContentType)
        ) {
          request.body = xml2js(request.stringBody, {
            compact: true
          });
          next();
        } else {
          next();
        }
      } else {
        next();
      }
    } catch (error: any) {
      this.emit('error', ServerErrorCodes.REQUEST_BODY_PARSE, error);
      next();
    }
  }

  /**
   * ### Middleware ###
   * Parse entering request body
   *
   * @param request
   * @param response
   * @param next
   */

  private parseBody = (
    request: Request,
    response: Response,
    next: NextFunction
  ) => {
    // Parse body as a raw string and JSON/form if applicable
    const requestContentType: string | undefined = request
      .header('Content-Type')
      ?.toLowerCase();

    // body was already parsed (e.g. by firebase), 'data' event will not be emitted (⚠️ request.body will always be an empty object in Firebase Functions, we have to check rawBody too)
    if (!!request.body && request.rawBody) {
      this.processRawBody(request, next, [request.rawBody], requestContentType);
    } else {
      const rawBody: Buffer[] = [];

      request.on('data', (chunk) => {
        rawBody.push(Buffer.from(chunk, 'binary'));
      });

      request.on('end', () => {
        this.processRawBody(request, next, rawBody, requestContentType);
      });
    }
  };

  /**
   * ### Middleware ###
   * Emit an event when response emit the 'close' event
   *
   * @param request
   * @param response
   * @param next
   */
  private logRequest = (
    request: Request,
    response: Response,
    next: NextFunction
  ) => {
    response.on('close', () => {
      const transaction = CreateTransaction(request, response);

      this.emit('transaction-complete', transaction);

      this.transactionLogs.push(transaction);

      // keep only the last n transactions
      if (this.transactionLogs.length > this.options.maxTransactionLogs) {
        this.transactionLogs = this.transactionLogs.slice(
          this.options.maxTransactionLogs * -1
        );
      }
    });

    next();
  };

  /**
   * ### Middleware ###
   * Add environment headers & proxy headers to the response
   *
   * @param request
   * @param response
   * @param next
   */
  private setResponseHeaders = (
    request: Request,
    response: Response,
    next: NextFunction
  ) => {
    this.setHeaders(this.environment.headers, response, request);

    next();
  };

  /**
   * Create a wildcard REST route that will handle all HTTP routes
   * We do it this way to be able to support dynamic route additions / deletions
   *
   * Note on performances: the path matching is done at runtime using path-to-regexp.
   * We tested the overhead of not caching the matchers with up to 10 000 routes, and it is
   * negligible (some extra milliseconds). We will reevaluate if any performance issue arises.
   *
   * @param server - server on which attach routes
   */
  private createRestRoutes(server: Application) {
    server.all(
      '*',
      (request: Request, response: Response, next: NextFunction) => {
        let matchingRoute: Route | null = null;
        let matchingRouteResponse: RouteResponse | null = null;
        let crudId: ReturnType<typeof crudRoutesBuilder>[number]['id'] | null =
          null;
        let matchingRoutePath = '';

        routesLoop: for (const route of this.effectiveRestRoutes) {
          // Get original path for logging/transactions
          const paths = preparePath(
            this.environment.endpointPrefix,
            route.endpoint
          );
          const routePath = paths.preparedPath;
          const originalPath = paths.original;

          if (route.type === RouteType.HTTP) {
            let routeUrlMatchResult;

            try {
              routeUrlMatchResult = pathMatch(routePath)(request.path);
            } catch (error: any) {
              if (error instanceof Error) {
                this.emit(
                  'error',
                  ServerErrorCodes.INVALID_ROUTE_PATH,
                  pathMatchErrorBuilder(error),
                  {
                    routePath,
                    routeUuid: route.uuid
                  }
                );
              }
              continue;
            }

            if (
              routeUrlMatchResult &&
              (route.method === 'all' ||
                route.method.toLowerCase() === request.method.toLowerCase())
            ) {
              if (!this.requestNumbers[route.uuid]) {
                this.requestNumbers[route.uuid] = 1;
              }

              request.params = routeUrlMatchResult.params as Record<
                string,
                string
              >;

              // Evaluate response rules inside the loop to support FALLBACK mode
              const triggeredRouteResponse = new ResponseRulesInterpreter(
                route.responses,
                fromExpressRequest(request),
                route.responseMode,
                this.environment,
                this.processedDatabuckets,
                this.globalVariables,
                this.options.envVarsPrefix,
                this.options.publicBaseUrl
              ).chooseResponse(this.requestNumbers[route.uuid]);

              // null response means no rule matched in FALLBACK mode, try next route
              if (triggeredRouteResponse) {
                matchingRoute = route;
                matchingRouteResponse = triggeredRouteResponse;
                matchingRoutePath = originalPath;
                break routesLoop;
              }
              // Continue to next route if null (FALLBACK mode)
            }
          } else if (route.type === RouteType.CRUD) {
            const crudRoutes = crudRoutesBuilder(routePath);

            for (const crudRoute of crudRoutes) {
              let crudUrlMatchResult;

              try {
                crudUrlMatchResult = pathMatch(crudRoute.path)(request.path);
              } catch (error: any) {
                if (error instanceof Error) {
                  this.emit(
                    'error',
                    ServerErrorCodes.INVALID_ROUTE_PATH,
                    pathMatchErrorBuilder(error),
                    {
                      routePath: crudRoute.path,
                      routeUuid: route.uuid
                    }
                  );
                }
                continue;
              }

              if (
                crudUrlMatchResult &&
                crudRoute.method.toLowerCase() === request.method.toLowerCase()
              ) {
                if (!this.requestNumbers[route.uuid]) {
                  this.requestNumbers[route.uuid] = 1;
                }
                request.params = crudUrlMatchResult.params as Record<
                  string,
                  string
                >;

                // Evaluate response rules inside the loop to support FALLBACK mode
                const triggeredRouteResponse = new ResponseRulesInterpreter(
                  route.responses,
                  fromExpressRequest(request),
                  route.responseMode,
                  this.environment,
                  this.processedDatabuckets,
                  this.globalVariables,
                  this.options.envVarsPrefix,
                  this.options.publicBaseUrl
                ).chooseResponse(this.requestNumbers[route.uuid]);

                // null response means no rule matched in FALLBACK mode, try next route
                if (triggeredRouteResponse) {
                  matchingRoute = route;
                  matchingRouteResponse = triggeredRouteResponse;
                  crudId = crudRoute.id;
                  matchingRoutePath = originalPath;
                  break routesLoop;
                }
                // Continue to next route if null (FALLBACK mode)
              }
            }
          }
        }

        if (matchingRoute && matchingRouteResponse) {
          request.effectiveRoute = matchingRoutePath;

          this.routeHandler(
            matchingRoute,
            matchingRouteResponse,
            request,
            response,
            crudId
          );

          return;
        }

        // if no route matched, go to next middleware (global error handler, or proxy)
        next();
      }
    );
  }

  /**
   * Creates websocket routes from the given set of routes.
   *
   */
  private createWebsocketRoutes() {
    if (this.effectiveWebSocketRoutes.length > 0) {
      this.effectiveWebSocketRoutes.forEach((wsRoute) => {
        this.createWebsocketRoute(wsRoute);
      });

      this.registerWebSocketUpgradeHandler();
    }
  }

  /**
   * Creates a single websocket route and adds it to the servers array.
   *
   * @param wsRoute
   */
  private createWebsocketRoute(wsRoute: Route) {
    const webSocketServer = new WebSocket.Server({
      noServer: true
    });

    this.webSocketServers.push({
      instance: webSocketServer,
      path: wsRoute.endpoint,
      routeUuid: wsRoute.uuid
    });

    webSocketServer.on(
      'connection',
      this.createWebSocketConnectionHandler(webSocketServer, wsRoute)
    );
  }

  /**
   * Registers the upgrade event handler for WebSocket connections.
   * This is attached to the server instance only once.
   */
  private registerWebSocketUpgradeHandler() {
    this.serverInstance.on('upgrade', this.webSocketUpgradeHandler);
  }

  private webSocketUpgradeHandler = (req, socket, head) => {
    const urlParsed = parseUrl(req.url || '', true);

    // check if the request is a websocket upgrade request
    if (req.headers.upgrade !== 'websocket') {
      socket.write(`HTTP/${req.httpVersion} 400 Bad Request\r\n`);
      socket.write('Content-Type: text/html\r\n');
      socket.write('Content-length: 72\r\n\r\n');
      socket.write(
        'Invalid WebSocket upgrade request: "Upgrade: websocket" header not found'
      );
      socket.destroy();

      return;
    }

    for (const wsServer of this.webSocketServers) {
      const paths = preparePath(this.environment.endpointPrefix, wsServer.path);
      let pathMatchResult;

      try {
        pathMatchResult = pathMatch(paths.preparedPath)(
          urlParsed.pathname || ''
        );
      } catch (error: any) {
        if (error instanceof Error) {
          this.emit(
            'error',
            ServerErrorCodes.INVALID_ROUTE_PATH,
            pathMatchErrorBuilder(error),
            {
              routePath: paths.original,
              routeUuid: wsServer.routeUuid
            }
          );
        }
        continue;
      }

      if (pathMatchResult) {
        req.params = pathMatchResult.params as Record<string, string>;

        wsServer.instance.handleUpgrade(req, socket, head, (client) => {
          wsServer.instance.emit('connection', client, req);
        });

        return;
      }
    }

    // if no route is matched (loop didn't return), close the connection
    socket.write(`HTTP/${req.httpVersion} 404 Not Found\r\n`);
    socket.write('Content-Type: text/html\r\n');
    socket.write('Content-length: 38\r\n\r\n');
    socket.write('No WebSocket route found for this path');
    socket.destroy();
  };

  /**
   * Creates a handler for a web socket connection received, if only any
   * of route is matched.
   *
   * @param webSocketServer
   * @param routeFor
   * @returns
   */
  private createWebSocketConnectionHandler(
    webSocketServer: WebSocketServer,
    routeFor: Route
  ) {
    return (socket: WebSocket, request: Request) => {
      const route = this.getRefreshedRoute(routeFor);

      if (!route) {
        this.emit('error', ServerErrorCodes.ROUTE_NO_LONGER_EXISTS, null, {
          routePath: routeFor.endpoint,
          routeUUID: routeFor.uuid
        });

        return;
      }

      const websocketUuid = generateUUID();
      const baseErrorMeta = {
        websocketUuid: websocketUuid,
        routeUUID: route.uuid,
        routePath: route.endpoint
      };

      const inflightRequest = CreateInFlightRequest(
        websocketUuid,
        request,
        route
      );
      this.emit('ws-new-connection', inflightRequest);

      let responseNumber = 1;

      // handle error event
      socket.on('error', (err) => {
        this.emit(
          'error',
          ServerErrorCodes.WS_SERVING_ERROR,
          err,
          baseErrorMeta
        );
      });

      // handle common close method.
      // There would be more close methods registered, if the route is in streaming mode.
      socket.on('close', (code, reason) => {
        this.emit(
          'ws-closed',
          inflightRequest,
          code,
          reason ? reason.toString('utf8') : null
        );
      });

      const serverRequest = fromWsRequest(request, route);

      // This is not waiting until a message from client. But will push messages as a stream.
      if (route.streamingMode === StreamingMode.BROADCAST) {
        this.handleBroadcastResponse(
          webSocketServer,
          socket,
          route,
          serverRequest,
          baseErrorMeta
        );

        return;
      } else if (route.streamingMode === StreamingMode.UNICAST) {
        this.handleOneToOneStreamingResponses(
          socket,
          route,
          request,
          baseErrorMeta
        );

        return;
      }

      socket.on('message', (data, isBinary) => {
        if (isBinary) {
          this.emit(
            'error',
            ServerErrorCodes.WS_UNSUPPORTED_CONTENT,
            null,
            baseErrorMeta
          );

          return;
        }

        const routeInMessage = this.getRefreshedRoute(route);

        // the route is not found. Skip reacting.
        if (!routeInMessage) {
          this.emit(
            'error',
            ServerErrorCodes.WS_UNKNOWN_ROUTE,
            null,
            baseErrorMeta
          );

          return;
        }

        // get the incoming message as string...
        const messageData = messageToString(data);
        this.emit('ws-message-received', inflightRequest, messageData);

        const enabledRouteResponse = new ResponseRulesInterpreter(
          routeInMessage.responses,
          serverRequest,
          routeInMessage.responseMode,
          this.environment,
          this.processedDatabuckets,
          this.globalVariables,
          this.options.envVarsPrefix,
          this.options.publicBaseUrl
        ).chooseResponse(responseNumber, messageData);

        if (!enabledRouteResponse) {
          // Do nothing?
          return;
        }

        responseNumber += 1;

        setTimeout(() => {
          const content = this.deriveFinalResponseContentForWebSockets(
            socket,
            routeInMessage,
            enabledRouteResponse,
            request,
            messageData
          );

          if (content) {
            socket.send(content || '', (err) => {
              if (err) {
                this.emit('error', ServerErrorCodes.WS_SERVING_ERROR, err, {
                  ...baseErrorMeta,
                  selectedResponseUUID: enabledRouteResponse.uuid,
                  selectedResponseLabel: enabledRouteResponse.label
                });
              }
            });
          }
        }, enabledRouteResponse.latency);
      });
    };
  }

  /**
   * Derive final delivery content for websocket response.
   *
   * If no content is returned, that means the relevant content has been served,
   * or a failure has occurred. These scenarios can happen with file body type
   * and should be handled properly by the callers.
   *
   * @param socket
   * @param route
   * @param enabledRouteResponse
   * @param request
   * @param data
   */
  private deriveFinalResponseContentForWebSockets(
    socket: WebSocket,
    route: Route,
    enabledRouteResponse: RouteResponse,
    request?: Request,
    data?: string,
    connectedRequest?: ServerRequest
  ): string | undefined {
    let content: any = enabledRouteResponse.body;
    let finalRequest = connectedRequest;

    finalRequest ??= request ? fromWsRequest(request, route, data) : undefined;

    if (
      enabledRouteResponse.bodyType === BodyTypes.DATABUCKET &&
      enabledRouteResponse.databucketID
    ) {
      const servedDatabucket = this.processedDatabuckets.find(
        (processedDatabucket) =>
          processedDatabucket.id === enabledRouteResponse.databucketID
      );

      if (servedDatabucket) {
        content = servedDatabucket.value;

        if (
          Array.isArray(content) ||
          typeof content === 'object' ||
          typeof content === 'boolean' ||
          typeof content === 'number'
        ) {
          content = JSON.stringify(content);
        }
      }
    } else if (
      enabledRouteResponse.bodyType === BodyTypes.FILE &&
      enabledRouteResponse.filePath
    ) {
      const filePath = this.getSafeFilePath(
        enabledRouteResponse.filePath,
        finalRequest
      );

      serveFileContentInWs(
        socket,
        route,
        enabledRouteResponse,
        this,
        filePath,
        (contentData: string) =>
          TemplateParser({
            shouldOmitDataHelper: false,
            content: contentData,
            environment: this.environment,
            processedDatabuckets: this.processedDatabuckets,
            globalVariables: this.globalVariables,
            request: finalRequest,
            envVarsPrefix: this.options.envVarsPrefix,
            publicBaseUrl: this.options.publicBaseUrl
          })
      );

      return;
    }

    if (!enabledRouteResponse.disableTemplating) {
      content = TemplateParser({
        shouldOmitDataHelper: false,
        content: content || '',
        environment: this.environment,
        processedDatabuckets: this.processedDatabuckets,
        globalVariables: this.globalVariables,
        request: finalRequest,
        envVarsPrefix: this.options.envVarsPrefix,
        publicBaseUrl: this.options.publicBaseUrl
      });
    }

    return content;
  }

  private handleBroadcastResponse(
    webSocketServer: WebSocketServer,
    socket: WebSocket,
    route: Route,
    request: ServerRequest,
    baseErrorMeta: any
  ) {
    const broadcastContext = BroadcastContext.getInstance();
    const handler: DelegatedBroadcastHandler = (
      _: number,
      enabledRouteResponse: RouteResponse
    ) => {
      // todo: do we need to take params from initial connection at all?
      const content =
        this.deriveFinalResponseContentForWebSockets(
          socket,
          route,
          enabledRouteResponse,
          undefined,
          undefined,
          request
        ) || '';

      if (!content) {
        return;
      }

      const errorMetaData = {
        ...baseErrorMeta,
        selectedResponseUUID: enabledRouteResponse.uuid,
        selectedResponseLabel: enabledRouteResponse.label
      };

      webSocketServer.clients.forEach((client) => {
        if (isWebSocketOpen(client)) {
          this.serveWsResponse(client, content, errorMetaData);
        }
      });
    };

    broadcastContext.registerRoute(
      route,
      {
        environment: this.environment,
        processedDatabuckets: this.processedDatabuckets,
        globalVariables: this.globalVariables,
        envVarPrefix: this.options.envVarsPrefix,
        publicBaseUrl: this.options.publicBaseUrl
      },
      request,
      handler
    );
  }

  /**
   * Handle streaming websocket responses.
   *
   * @param socket
   * @param route
   * @param request
   * @param baseErrorMeta
   */
  private handleOneToOneStreamingResponses(
    socket: WebSocket,
    route: Route,
    request: Request,
    baseErrorMeta: any
  ) {
    let responseNumber = 1;

    const intervalRef = setInterval(() => {
      const enabledRouteResponse = new ResponseRulesInterpreter(
        route.responses,
        fromWsRequest(request, route),
        route.responseMode,
        this.environment,
        this.processedDatabuckets,
        this.globalVariables,
        this.options.envVarsPrefix,
        this.options.publicBaseUrl
      ).chooseResponse(responseNumber);

      if (!enabledRouteResponse) {
        return;
      }

      const content =
        this.deriveFinalResponseContentForWebSockets(
          socket,
          route,
          enabledRouteResponse,
          request
        ) || '';

      responseNumber += 1;

      if (!content) {
        return;
      }

      const errorMetaData = {
        ...baseErrorMeta,
        selectedResponseUUID: enabledRouteResponse.uuid,
        selectedResponseLabel: enabledRouteResponse.label
      };

      if (route.streamingMode === StreamingMode.UNICAST) {
        if (isWebSocketOpen(socket)) {
          this.serveWsResponse(socket, content, errorMetaData);
        }
      }
    }, getSafeStreamingInterval(route.streamingInterval));

    socket.on('close', () => {
      // close any interval data pushes
      if (intervalRef) {
        clearInterval(intervalRef);
      }
    });
  }

  /**
   * Sends given response data to the socket client.
   *
   * @param client
   * @param content
   * @param errorMetaData
   */
  private serveWsResponse(
    client: WebSocket,
    content: string,
    errorMetaData: any
  ) {
    client.send(content, (err) => {
      if (err) {
        this.emit(
          'error',
          ServerErrorCodes.WS_SERVING_ERROR,
          err,
          errorMetaData
        );
      }
    });
  }

  private routeHandler(
    route: Route,
    triggeredRouteResponse: RouteResponse,
    request: Request,
    response: Response,
    crudId?: ReturnType<typeof crudRoutesBuilder>[number]['id'] | null
  ) {
    generateRequestDatabuckets(
      route,
      this.environment,
      request,
      this.processedDatabuckets,
      this.globalVariables,
      this.options,
      () => {
        this.emitProcessedDatabuckets();
      }
    );

    this.requestNumbers[route.uuid] += 1;

    // save route and response UUIDs for logs (only in desktop app)
    if (route.uuid && triggeredRouteResponse.uuid) {
      response.routeUUID = route.uuid;
      response.routeResponseUUID = triggeredRouteResponse.uuid;
    }

    const latency = getLatency(
      triggeredRouteResponse.latency,
      this.options.enableRandomLatency
    );

    // add route latency if any
    setTimeout(() => {
      const contentType = GetRouteResponseContentType(
        this.environment,
        triggeredRouteResponse
      );
      const routeContentType = GetContentType(triggeredRouteResponse.headers);

      // set http code
      response.status(triggeredRouteResponse.statusCode);

      this.setHeaders(triggeredRouteResponse.headers, response, request);
      if (this.options.enableRouteMetadataHeaders) {
        this.setRouteMetadataHeaders(route, triggeredRouteResponse, response);
      }

      // send the file
      if (
        triggeredRouteResponse.bodyType === BodyTypes.FILE &&
        triggeredRouteResponse.filePath
      ) {
        this.sendFile(
          route,
          triggeredRouteResponse,
          routeContentType,
          request,
          response
        );

        // serve inline body or databucket
      } else {
        let templateParse = true;

        if (contentType.includes('application/json')) {
          response.set('Content-Type', 'application/json');
        }

... [truncated, file is 73699 chars]
```

### packages/commons-server/src/libs/utils.ts
```
import { search } from '@jmespath-community/jmespath';
import {
  Callback,
  generateUUID,
  Header,
  InFlightRequest,
  InvokedCallback,
  Methods,
  ParsedJSONBodyMimeTypes,
  ParsedXMLBodyMimeTypes,
  Route,
  stringIncludesArrayItems,
  Transaction
} from '@mockoon/commons';
import { Request, Response } from 'express';
import { SafeString } from 'handlebars';
import {
  IncomingHttpHeaders,
  IncomingMessage,
  OutgoingHttpHeaders
} from 'http';
import { JSONPath } from 'jsonpath-plus';
import { get as objectGet } from 'object-path';
import { isAbsolute, resolve } from 'path';
import { parse as parseUrl, URL } from 'url';
import { xml2js } from 'xml-js';
import { brotliDecompressSync, inflateSync, unzipSync } from 'zlib';
import { ServerRequest } from './requests';

export { lookup as mimeTypeLookup } from 'mime-types';
export { get as objectGetPath } from 'object-path';

/**
 * Transform http headers objects to Mockoon's Header key value object
 *
 * @param object
 */
const TransformHeaders = (
  headers: IncomingHttpHeaders | OutgoingHttpHeaders
): Header[] =>
  Object.keys(headers).reduce<Header[]>((newHeaders, key) => {
    const headerValue = headers[key];
    let value = '';

    if (headerValue !== undefined) {
      if (Array.isArray(headerValue)) {
        value = headerValue.join(',');
      } else {
        value = headerValue.toString();
      }
    }

    newHeaders.push({ key, value });

    return newHeaders;
  }, []);

/**
 * Sort by ascending order
 *
 * @param a
 * @param b
 */
const AscSort = (a: { key: string }, b: { key: string }) => {
  if (a.key < b.key) {
    return -1;
  } else {
    return 1;
  }
};

/**
 * Check if an Object or Array is empty
 *
 * @param obj
 */
export const IsEmpty = (obj: any) =>
  (Array.isArray(obj) || (obj instanceof Object && obj !== null)) &&
  !Object.entries(obj || {}).length;

/**
 * Decompress body based on content-encoding
 *
 * Zstd support requires Node.js 22 or higher, thus it is conditionally applied
 *
 * @param response
 */
export const DecompressBody = (response: Response) => {
  if (!response.body) {
    return response.body;
  }

  const contentEncoding = response.getHeader('content-encoding');
  let body = response.body;

  switch (contentEncoding) {
    case 'gzip':
      body = unzipSync(body);
      break;
    case 'br':
      body = brotliDecompressSync(body);
      break;
    case 'deflate':
      body = inflateSync(body);
      break;
    case 'zstd':
      {
        // eslint-disable-next-line
        const zlib = require('zlib');

        if (zlib.zstdDecompressSync) {
          body = zlib.zstdDecompressSync(body);
        }
      }
      break;
    default:
      break;
  }

  return body.toString('utf-8');
};

/**
 * Returns true if given HTTP method is a body supporting one. Otherwise false.
 * @param method
 */
export function isBodySupportingMethod(method: Methods): boolean {
  return [Methods.put, Methods.post, Methods.patch].includes(method);
}

/**
 * Creates a callback invocation record which has information
 * about the invoked details.
 * @param callback
 * @param url
 * @param requestBody
 * @param requestHeaders
 * @param fetchResponse
 * @param responseBody
 */
export function CreateCallbackInvocation(
  callback: Callback,
  url: string,
  requestBody: string | null | undefined,
  requestHeaders: Header[],
  fetchResponse: globalThis.Response,
  responseBody: any
): InvokedCallback {
  const resHeadersObj = Object.fromEntries(fetchResponse.headers.entries());

  return {
    name: callback.name,
    url,
    method: callback.method,
    requestBody,
    requestHeaders,
    status: fetchResponse.status,
    responseBody,
    responseHeaders: Object.keys(resHeadersObj).map(
      (k) => ({ key: k, value: resHeadersObj[k] }) as Header
    )
  };
}

/**
 * Creates in-flight request object.
 *
 * @param requestUuid
 * @param request
 * @param route
 */
export function CreateInFlightRequest(
  requestUuid: string,
  request: IncomingMessage,
  route: Route
): InFlightRequest {
  const parsedUrl = parseUrl(request.url || '', true);

  return {
    uuid: requestUuid,
    routeUUID: route.uuid,
    request: {
      method: (request.method as keyof typeof Methods) || 'get',
      urlPath: parsedUrl.pathname,
      route: route.endpoint,
      headers: TransformHeaders(request.headers).sort(AscSort),
      body: request.body,
      query: parsedUrl.search,
      params: [], // we don't support params yet
      queryParams: parsedUrl.query
        ? Object.keys(parsedUrl.query).map((k) => ({
            name: k,
            value: parsedUrl.query[k]
          }))
        : []
    },
    completed: false
  };
}

/**
 * Create a Transaction object from express req/res.
 * To be used after the response closes
 *
 * @param request
 * @param response
 */
export function CreateTransaction(
  request: Request,
  response: Response
): Transaction {
  const requestUrl = new URL(request.originalUrl, 'http://localhost/');
  let queryString = requestUrl.search.slice(1);
  try {
    queryString = decodeURI(queryString);
  } catch (_error) {}

  return {
    request: {
      method: request.method.toLowerCase() as keyof typeof Methods,
      urlPath: requestUrl.pathname,
      route: request.effectiveRoute ? request.effectiveRoute : null,
      params: request.params
        ? Object.keys(request.params).map((paramName) => ({
            name: paramName,
            value: request.params[paramName]
          }))
        : [],
      query: requestUrl ? queryString : null,
      queryParams: request.query,
      body: request.stringBody,
      headers: TransformHeaders(request.headers).sort(AscSort)
    },
    response: {
      statusCode: response.statusCode,
      statusMessage: response.statusMessage,
      headers: TransformHeaders(response.getHeaders()).sort(AscSort),
      body: DecompressBody(response)
    },
    routeResponseUUID: response.routeResponseUUID,
    routeUUID: response.routeUUID,
    proxied: request.proxied || false,
    timestampMs: Date.now(),
    uuid: generateUUID()
  };
}

/**
 * Convert a string to base64
 *
 * @param text
 */
export const ToBase64 = (text: string): string =>
  Buffer.from(text, 'utf-8').toString('base64');

/**
 * Convert a string to base64url
 *
 * @param text
 */
export const ToBase64URL = (text: string): string =>
  Buffer.from(text, 'utf-8').toString('base64url');

/**
 * Convert base64 to a string
 *
 * @param base64
 */
export const FromBase64 = (base64: string): string =>
  Buffer.from(base64, 'base64').toString('utf-8');

/**
 * Convert base64url to a string
 *
 * @param base64url
 */
export const FromBase64URL = (base64url: string): string =>
  Buffer.from(base64url, 'base64url').toString('utf-8');

/**
 * Extract the string value from a SafeString
 *
 * @param value
 * @returns
 */
export const fromSafeString = (value: any | SafeString) =>
  value instanceof SafeString ? value.toString() : value;

/**
 * Parse a number from a SafeString if needed.
 *
 * @param text
 * @returns
 */
export const numberFromSafeString = (text: string | SafeString) => {
  const parsedText = text instanceof SafeString ? text.toString() : text;

  return parseInt(parsedText, 10);
};

/**
 *
 * @param text
 * @returns object | null
 */
export const objectFromSafeString = (text: string | SafeString) => {
  const parsedText = text instanceof SafeString ? text.toString() : text;
  // Remove any escape slashes used to escape double-quotes or single-quotes
  // (Check test case).
  // Surround all object keys with double-quotes to make it valid JSON text.
  const objectText = parsedText
    .replace(/\\/g, '')
    .replace(/(['"])?([a-zA-Z0-9_]+)(['"])?:/g, '"$2": ');
  try {
    return JSON.parse(objectText);
  } catch (_error) {
    return null;
  }
};

/**
 * Resolve a file path relatively to the current environment folder if provided
 */
export const resolvePathFromEnvironment = (
  filePath: string,
  environmentDirectory?: string
) => {
  if (environmentDirectory && !isAbsolute(filePath)) {
    return resolve(environmentDirectory, filePath);
  }

  return filePath;
};

/**
 * Convert an object path (for the object-path lib) containing escaped dots '\.'
 * to an array of strings to allow fetching properties containing dots.
 *
 * Example:
 * 'get.a.property\.with\.dots => ['get', 'a', 'property.with.dots']
 *
 * To query an object like this:
 *
 * ```
 * {
 *   get: {
 *     a: {
 *       'property.with.dots': "value"
 *     }
 *   }
 * }
 * ```
 * @param str
 */
export const convertPathToArray = (str: string): string | string[] => {
  if (str.includes('\\.')) {
    return str
      .replace(/\\\./g, '%#%')
      .split('.')
      .map((s) => s.replace(/%#%/g, '.'));
  }

  return str;
};

/**
 * Escape special characters in a string to be used in a regex
 * Taken from Lodash escapeRegExp
 *
 * @param text
 * @returns
 */
export const escapeRegExp = (text: string) => {
  return text.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&');
};

/**
 * Perform a full text search on an object. The object can be any valid JSON type
 *
 * @param object
 * @param query
 * @returns
 */
export const fullTextSearch = (object: unknown, query: string): boolean => {
  if (typeof object === 'object' || typeof object === 'boolean') {
    return Object.values(object ?? []).some((value) =>
      fullTextSearch(value, query)
    );
  }

  return new RegExp(escapeRegExp(query), 'i').test(String(object));
};

/**
 * Validates a given JSONPath string to check if the filter expressions are safe for evaluation.
 * If no filter expression is found in the path, it returns the path as valid.
 * If filter expressions are found, each one is checked against a regular expression to ensure it is safe.
 * The function returns a boolean indicating whether the path is valid.
 *
 * If path is too long, it is considered unsafe due to the time complexity of the hasFilter check.
 *
 * @param {string} path - The JSONPath string to be validated.
 * @returns {boolean} - whether JSONPath string is safe or not
 */
export const isSafeJSONPath = (path: string): boolean => {
  /* filterRE is used to match each individual filter expression */
  const FILTER_RE = new RegExp(
    '^' +
      // eventually wrapped in parentheses: e.g. (@property === 'price')
      '[(]*' +
      // Group 1: Allow l.h.s names like - @price or @.group or @['Account Name'] or length-1 or @.match(/regex/)
      // Keys with spaces are allowed
      "(@{0,1}\\.{0,1}[_a-zA-Z0-9\\-\\[\\]\\.]*|@{0,1}\\['[_a-zA-Z0-9\\s]*'\\]|@[a-zA-Z0-9_\\s'\\-\\[\\]\\.]*.match\\(.*\\))" +
      '\\s*' + // ignore any whitespaces before the operator
      // Group 2 (optional): Supported operators ==, !=, ===, !==, <, >, <=, >=
      '(==|!=|===|!==|<|<=|>|>=)?' +
      '\\s*' + // ignore any whitespaces after the operator
      // Group 3 (optional): Supported r.h.s - single/double quoted strings, numbers, boolean, undefined,
      // reference to other properties like @. or $.
      // Keys with spaces are allowed
      "(\"[^\"]*\"|'[^']*'|[0-9.]+|@{0,1}\\${0,1}[\\.a-zA-Z0-9_\\[\\]\\s']*|true|false|undefined)?" +
      // eventually wrapped in parentheses: e.g. (@property === 'price')
      '[)]*' +
      '$'
  );

  /*
   * groupRE is used to capture each individual filter in case && or || are being used
   * Returns individual filter expression groups (value without ())
   */
  const GROUP_RE = new RegExp(
    '\\s*&&\\s*|\\s*\\|\\|\\s*', // Non capturing group matching ' && ' or ' || ' or EOL
    'g'
  );

  if (path.length > 1000) {
    return false;
  }

  const hasFilter = (/\((.*)\)/.exec(path) ?? [])[1];

  if (!hasFilter) {
    return true;
  }

  const filters = hasFilter.split(GROUP_RE);

  if (!filters) {
    return true;
  }

  let isValid = true;

  // Recursively test each filter expression
  for (let filter of filters) {
    filter = filter.trim();

    if (!FILTER_RE.test(filter)) {
      isValid = false;
    }
  }

  return isValid;
};

/**
 * Look for a value in an object or array using a path (dot notation or JSONPath).
 * If no path is provided, return the full data.
 * If the value is not found, return the default value.
 *
 * @param data
 * @param path
 * @param defaultValue
 * @returns
 */
export const getValueFromPath = (
  data: any,
  path: string,
  defaultValue: any
) => {
  if (
    (Array.isArray(data) || typeof data === 'object') &&
    typeof path === 'string' &&
    path !== ''
  ) {
    let foundValue: any;

    // Added wrap = false (Check https://github.com/mockoon/mockoon/issues/1297)
    if (path.startsWith('$')) {
      if (isSafeJSONPath(path)) {
        foundValue = JSONPath({ json: data, path: path, wrap: false });
      }
    } else {
      foundValue = objectGet(data, convertPathToArray(path));
    }

    return foundValue !== undefined ? foundValue : defaultValue;
  }

  return data;
};

/**
 * Look for a value in an object or array using JMESPath.
 *
 * @param data
 * @param path
 * @param defaultValue
 * @returns
 */
getValueFromPath.jmesPath = (data: any, path: string, defaultValue: any) => {
  if (
    (Array.isArray(data) || typeof data === 'object') &&
    typeof path === 'string' &&
    path !== ''
  ) {
    let foundValue: any;

    try {
      foundValue = search(data, path);
    } catch (_error) {
      // silently fail if the path is invalid (same as JSONPath)
    }

    // JMESPath returns null if the value is not found (unlike JSONPath which returns undefined)
    return foundValue ?? defaultValue;
  }

  return data;
};

/**
 * Look for a value in an object or array using JSONPath.
 *
 * @param data
 * @param path
 * @param defaultValue
 * @returns
 */
getValueFromPath.jsonPath = (data: any, path: string, defaultValue: any) => {
  if (
    (Array.isArray(data) || typeof data === 'object') &&
    typeof path === 'string' &&
    path !== ''
  ) {
    let foundValue: any;

    if (isSafeJSONPath(path)) {
      // Added wrap = false (Check https://github.com/mockoon/mockoon/issues/1297)
      foundValue = JSONPath({ json: data, path: path, wrap: false });
    }

    return foundValue !== undefined ? foundValue : defaultValue;
  }

  return data;
};

/**
 * Get a value from an object or array using object-path.
 *
 * @param data
 * @param path
 * @param defaultValue
 * @returns
 */
getValueFromPath.objectPath = (data: any, path: string, defaultValue: any) => {
  if (
    (Array.isArray(data) || typeof data === 'object') &&
    typeof path === 'string' &&
    path !== ''
  ) {
    const foundValue = objectGet(data, convertPathToArray(path));

    return foundValue !== undefined ? foundValue : defaultValue;
  }

  return data;
};

/**
 * Returns data based on the content type.
 *
 * @param data
 * @param contentType
 */
const parseByContentType = (data: string, contentType?: string): any => {
  if (contentType) {
    if (stringIncludesArrayItems(ParsedJSONBodyMimeTypes, contentType)) {
      return JSON.parse(data || '{}');
    } else if (stringIncludesArrayItems(ParsedXMLBodyMimeTypes, contentType)) {
      return xml2js(data, { compact: true });
    }
  }

  return data;
};

/**
 * Parses a websocket message based on the content-type specified in the socket connection.
 * We have to use this function, because this has to be called when creating a Mockoon
 * ServerRequest object from a WS connection request.
 *
 * @param messageData
 * @param request
 */
export const parseWebSocketMessage = (
  messageData: string,
  request?: IncomingMessage
): any => {
  const contentType = request?.headers['content-type'];

  return parseByContentType(messageData, contentType);
};

/**
 * Returns appropriate object by parsing it as necessary.
 * This will check content-type header and will parse messageData based on the type.
 *
 * @param data
 * @param request
 */
export const parseRequestMessage = (
  data: string,
  request?: ServerRequest
): any => {
  const contentType = request?.header('content-type') as string;

  return parseByContentType(data, contentType);
};

/**
 * Validate status code (100-999)
 *
 * @param statusCode - The status code to validate
 * @returns boolean
 */
export const isValidStatusCode = (statusCode: number): boolean => {
  return Number.isInteger(statusCode) && statusCode >= 100 && statusCode <= 999;
};

```

### packages/commons/src/models/server.model.ts
```
import { FakerAvailableLocales } from './faker.model';
import { Header, Methods } from './route.model';

export type ProcessedDatabucket = {
  uuid: string;
  id: string;
  name: string;
  value: any;
  parsed: boolean;
  validJson: boolean;
};

export type ProcessedDatabucketWithoutValue = Omit<
  ProcessedDatabucket,
  'value'
>;

/**
 * Object containing invoked callback details.
 */
export type InvokedCallback = {
  name: string;
  url: string;
  method: keyof typeof Methods;
  requestHeaders: Header[];
  requestBody: any;
  status: number;
  responseBody: any;
  responseHeaders: Header[];
};

/**
 * Represents an in-flight request.
 * WebSockets requests or any other long-living
 * connections can be considered as in-flight requests.
 */
export type InFlightRequest = {
  request: {
    method: keyof typeof Methods;
    urlPath: string | null;
    route: string | null;
    params?: { name: string; value: string }[];
    query?: string | null;
... [truncated, file is 4423 chars]
```

### packages/commons/src/utils/utils.ts
[omitted: context budget exhausted]

### packages/serverless/README.md
[omitted: context budget exhausted]

### packages/serverless/src/libs/serverless.ts
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
### packages/app/src/renderer/app/app.component.ts
```
import { AsyncPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  OnInit,
  inject
} from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Environment } from '@mockoon/commons';
import { NgbToast } from '@ng-bootstrap/ng-bootstrap';
import {
  Observable,
  auditTime,
  combineLatest,
  delay,
  distinctUntilChanged,
  from,
  fromEvent,
  map,
  of,
  startWith,
  switchMap,
  tap
} from 'rxjs';
import { EnvironmentCallbacksComponent } from 'src/renderer/app/components/environment-callbacks/environment-callbacks.component';
import { EnvironmentDatabucketsComponent } from 'src/renderer/app/components/environment-databuckets/environment-databuckets.component';
import { EnvironmentHeadersComponent } from 'src/renderer/app/components/environment-headers/environment-headers.component';
import { EnvironmentLogsComponent } from 'src/renderer/app/components/environment-logs/environment-logs.component';
import { EnvironmentProxyComponent } from 'src/renderer/app/components/environment-proxy/environment-proxy.component';
import { EnvironmentRoutesComponent } from 'src/renderer/app/components/environment-routes/environment-routes.component';
import { EnvironmentSettingsComponent } from 'src/renderer/app/components/environment-settings/environment-settings.component';
import { FooterComponent } from 'src/renderer/app/components/footer/footer.component';
import { HeaderComponent } from 'src/renderer/app/components/header/header.component';
import { EnvironmentsMenuComponent } from 'src/renderer/app/components/menus/environments-menu/environments-menu.component';
import { TourComponent } from 'src/renderer/app/components/tour/tour.component';
import { ViewsNameType } from 'src/renderer/app/models/store.model';
import { Toast } from 'src/renderer/app/models/toasts.model';
import { AppQuitService } from 'src/renderer/app/services/app-quit.services';
import { DeployService } from 'src/renderer/app/services/deploy.service';
import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
import { LoggerService } from 'src/renderer/app/services/logger-service';
import { MainApiListenerService } from 'src/renderer/app/services/main-api-listener.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { RemoteConfigService } from 'src/renderer/app/services/remote-config.service';
import { ServerService } from 'src/renderer/app/services/server.service';
import { SettingsService } from 'src/renderer/app/services/settings.service';
import { SyncService } from 'src/renderer/app/services/sync.service';
import { ToastsService } from 'src/renderer/app/services/toasts.service';
import { TourService } from 'src/renderer/app/services/tour.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { UserService } from 'src/renderer/app/services/user.service';
import { Store } from 'src/renderer/app/stores/store';
import { environment } from 'src/renderer/environments/environment';
import { OfflineBannerComponent } from './components/offline-banner/offline-banner.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgbToast,
    EnvironmentsMenuComponent,
    HeaderComponent,
    EnvironmentRoutesComponent,
    EnvironmentDatabucketsComponent,
    EnvironmentCallbacksComponent,
    EnvironmentHeadersComponent,
    EnvironmentLogsComponent,
    EnvironmentProxyComponent,
    EnvironmentSettingsComponent,
    FooterComponent,
    TourComponent,
    AsyncPipe,
    OfflineBannerComponent
  ]
})
export class AppComponent implements OnInit {
  private environmentsService = inject(EnvironmentsService);
  private store = inject(Store);
  private toastService = inject(ToastsService);
  private uiService = inject(UIService);
  private mainApiListenerService = inject(MainApiListenerService);
  private settingsService = inject(SettingsService);
  private appQuitService = inject(AppQuitService);
  private userService = inject(UserService);
  private title = inject(Title);
  private tourService = inject(TourService);
  private remoteConfigService = inject(RemoteConfigService);
  private syncService = inject(SyncService);
  private deployService = inject(DeployService);
  private serverService = inject(ServerService);
  private mainApiService = inject(MainApiService);
  private loggerService = inject(LoggerService);
  public activeEnvironment$: Observable<Environment>;
  public activeView$: Observable<ViewsNameType>;
  public displayOfflineBanner$ = combineLatest([
    this.store.selectIsActiveEnvironmentEditable(),
    this.store.select('sync').pipe(
      map((sync) => sync?.lastDisconnectedAt),
      distinctUntilChanged()
    )
  ]).pipe(
    auditTime(0),
    switchMap(([isEditable, lastDisconnectedAt]) => {
      if (isEditable) {
        return of(false);
      }
      if (lastDisconnectedAt === null) {
        return of(true).pipe(delay(6000));
      }

      const elapsed = Date.now() - lastDisconnectedAt;

      if (elapsed >= 6000) {
        return of(true);
      }

      return of(true).pipe(delay(6000 - elapsed));
    }),
    // Hide the banner during the initial async pipe `null` state to avoid
    // flashing it before the first real emission.
    startWith(false)
  );
  public scrollToBottom = this.uiService.scrollToBottom;
  public toasts$: Observable<Toast[]>;
  public os: string;

  /**
   * Refresh the deploy instances and the user information
   * when the page becomes visible
   */
  @HostListener('document:visibilitychange')
  public documentVisibilityChange() {
    const user = this.store.get('user');

    if (document.visibilityState === 'visible' && user) {
      this.userService.getUserInfo().subscribe();

      if (user.plan !== 'FREE' && user.plan !== 'SOLO') {
        this.deployService.getInstances().subscribe();
      }
    }
  }

  @HostListener('document:keydown', ['$event'])
  public globalKeyListener(event: KeyboardEvent) {
    if (
      ((event.ctrlKey && this.os !== 'darwin') ||
        (event.metaKey && this.os === 'darwin')) &&
      event.key.toLowerCase() === 'p'
    ) {
      event.preventDefault();
      this.uiService.openModal('commandPalette');
    }

    if (this.tourService.isInProgress()) {
      if (event.key === 'ArrowLeft') {
        this.tourService.previous();
      } else if (event.key === 'ArrowRight') {
        this.tourService.next();
      } else if (event.key === 'Escape') {
        this.tourService.stop();
      }
    }
  }

  ngOnInit() {
    this.settingsService.monitorSettings().subscribe();
    this.settingsService.loadSettings().subscribe();
    this.settingsService.saveSettings().subscribe();
    this.environmentsService.loadEnvironments().subscribe();
    this.environmentsService.saveEnvironments().subscribe();
    this.environmentsService.listenServerTransactions().subscribe();
    this.appQuitService.init().subscribe();
    this.remoteConfigService.init().subscribe();
    this.userService.init().subscribe();
    this.syncService.init().subscribe();
    this.deployService.init().subscribe();
    this.mainApiListenerService.init();
    this.serverService.init().subscribe();

    if (environment.web) {
      this.userService.webAuthHandler().subscribe();
    }

    this.loggerService.logMessage('info', 'INITIALIZING_APP');

    from(this.mainApiService.invoke('APP_GET_OS'))
      .pipe(
        tap((os) => {
          this.os = os;
        })
      )
      .subscribe();

    /**
     * Listen to online event to reload user and trigger the Firebase auth state change
     */
    fromEvent(window, 'online')
      .pipe(switchMap(() => this.userService.reloadUser()))
      .subscribe();

    this.activeEnvironment$ = this.store.selectActiveEnvironment().pipe(
      tap((activeEnvironment) => {
        this.title.setTitle(
          `${environment.production ? '' : ' [DEV]'}Mockoon${
            activeEnvironment ? ' - ' + activeEnvironment.name : ''
          }`
        );
      })
    );
    this.activeView$ = this.store.select('activeView');
    this.toasts$ = this.store.select('toasts');
  }

  /**
   * Pass remove event to toast service
   */
  public removeToast(toastUUID: string) {
    this.toastService.removeToast(toastUUID);
  }
}

```

### packages/app/src/renderer/app/services/environments.service.ts
```
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import {
  EnvironmentsListPayload,
  getEnvironmentByteSize
} from '@mockoon/cloud';
import {
  BuildCRUDRoute,
  BuildCallback,
  BuildDatabucket,
  BuildDemoEnvironment,
  BuildEnvironment,
  BuildFolder,
  BuildHTTPRoute,
  BuildHeader,
  BuildRouteResponse,
  BuildWebSocketRoute,
  Callback,
  CloneCallback,
  CloneDataBucket,
  CloneObject,
  CloneRouteResponse,
  DataBucket,
  Environment,
  EnvironmentDefault,
  Folder,
  Header,
  HighestMigrationId,
  INDENT_SIZE,
  OpenApiConverter,
  ReorderAction,
  ReorderableContainers,
  Route,
  RouteDefault,
  RouteResponse,
  RouteResponseDefault,
  RouteSchema,
  RouteType,
  deterministicStringify,
  generateUUID
} from '@mockoon/commons';
import {
  BehaviorSubject,
  EMPTY,
  Observable,
  concat,
  forkJoin,
  from,
  of,
  throwError,
  zip
} from 'rxjs';
import {
  catchError,
  debounceTime,
  filter,
  first,
  map,
  mergeMap,
  pairwise,
  startWith,
  switchMap,
  tap,
  withLatestFrom
} from 'rxjs/operators';
import { FocusableInputs } from 'src/renderer/app/enums/ui.enum';
import { CurlCommandBuilder } from 'src/renderer/app/libs/curl-command-builder.lib';
import {
  HumanizeText,
  environmentHasRoute,
  isRouteDuplicates,
  triggerBrowserDownload
} from 'src/renderer/app/libs/utils.lib';
import {
  CallbackResponseUsage,
  CallbackSpecTabNameType,
  CallbackTabsNameType,
  CallbackUsage
} from 'src/renderer/app/models/callback.model';
import { DataSubject } from 'src/renderer/app/models/data.model';
import { EnvironmentLog } from 'src/renderer/app/models/environment-logs.model';
import { MessageCodes } from 'src/renderer/app/models/messages.model';
import { OpenApiReimportPlan } from 'src/renderer/app/models/openapi.model';
import {
  EnvironmentLogsTabsNameType,
  TabsNameType,
  ViewsNameType
} from 'src/renderer/app/models/store.model';
import { DataService } from 'src/renderer/app/services/data.service';
import { DialogsService } from 'src/renderer/app/services/dialogs.service';
import { EventsService } from 'src/renderer/app/services/events.service';
import { LoggerService } from 'src/renderer/app/services/logger-service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { ServerService } from 'src/renderer/app/services/server.service';
import { StorageService } from 'src/renderer/app/services/storage.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import {
  Actions,
  addCallbackAction,
  addDatabucketAction,
  addEnvironmentAction,
  addFolderAction,
  addRouteAction,
  addRouteResponseAction,
  convertEnvironmentToLocalAction,
  logRequestAction,
  navigateEnvironmentsAction,
  refreshEnvironmentAction,
  reloadEnvironmentAction,
  removeCallbackAction,
  removeDatabucketAction,
  removeEnvironmentAction,
  removeFolderAction,
  removeRouteAction,
  removeRouteResponseAction,
  reorderCallbacksAction,
  reorderDatabucketsAction,
  reorderEnvironmentsAction,
  reorderRouteResponsesAction,
  reorderRoutesAction,
  setActiveCallbackAction,
  setActiveDatabucketAction,
  setActiveEnvironmentAction,
  setActiveEnvironmentLogTabAction,
  setActiveEnvironmentLogUUIDAction,
  setActiveRouteAction,
  setActiveRouteResponseAction,
  setActiveTabAction,
  setActiveTabInCallbackViewAction,
  setActiveViewAction,
  startEntityDuplicationToAnotherEnvironmentAction,
  updateCallbackAction,
  updateDatabucketAction,
  updateEnvironmentAction,
  updateFolderAction,
  updateRouteAction,
  updateRouteResponseAction,
  updateSettingsAction,
  updateUIStateAction
} from 'src/renderer/app/stores/actions';
import { ReducerDirectionType } from 'src/renderer/app/stores/reducer';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';
import { EnvironmentDescriptor } from 'src/shared/models/settings.model';

@Injectable({
  providedIn: 'root'
})
export class EnvironmentsService {
  private dataService = inject(DataService);
  private eventsService = inject(EventsService);
  private store = inject(Store);
  private serverService = inject(ServerService);
  private uiService = inject(UIService);
  private storageService = inject(StorageService);
  private dialogsService = inject(DialogsService);
  private http = inject(HttpClient);
  private mainApiService = inject(MainApiService);
  private loggerService = inject(LoggerService);

  private environmentChangesNotified = false;
  private environmentChanges$ = new BehaviorSubject<
    {
      UUID: string;
      environmentPath: string;
      name: string;
    }[]
  >([]);
  private isWeb = Config.isWeb;

  /**
   * Load environments after waiting for the settings to load
   *
   * @returns
   */
  public loadEnvironments() {
    return forkJoin([
      this.store.select('settings').pipe(
        filter((settings) => !!settings),
        first()
      ),
      from(this.mainApiService.invoke('APP_BUILD_STORAGE_FILEPATH', 'demo'))
    ]).pipe(
      switchMap(([settings, demoFilePath]) => {
        if (!settings.environments.length && !settings.welcomeShown) {
          if (this.isWeb) {
            return of({
              settings,
              environmentsData: []
            });
          } else {
            this.loggerService.logMessage(
              'info',
              'FIRST_LOAD_DEMO_ENVIRONMENT'
            );
            const defaultEnvironment = BuildDemoEnvironment();

            return of({
              settings,
              environmentsData: [
                {
                  environment: defaultEnvironment,
                  environmentDescriptor: {
                    uuid: defaultEnvironment.uuid,
                    path: demoFilePath,
                    cloud: false,
                    lastServerHash: null
                  } as EnvironmentDescriptor
                }
              ]
            });
          }
        }

        return forkJoin(
          settings.environments.map((environmentDescriptor) =>
            this.storageService
              .loadEnvironment(environmentDescriptor.path)
              .pipe(
                map((environment) =>
                  environment
                    ? {
                        environment,
                        environmentDescriptor
                      }
                    : null
                )
              )
          )
        ).pipe(map((environmentsData) => ({ settings, environmentsData })));
      }),
      // filter empty environments (file not found) and environments migrated with more recent app version
      map(({ settings, environmentsData }) => ({
        settings,
        environmentsData: environmentsData.filter(
          (environmentData) =>
            !!environmentData &&
            environmentData.environment.lastMigration <= HighestMigrationId
        )
      })),
      tap(({ settings, environmentsData }) => {
        environmentsData.forEach((environmentData) => {
          environmentData.environment =
            this.dataService.migrateAndValidateEnvironment(
              environmentData.environment
            );

          this.store.update(
            addEnvironmentAction(environmentData.environment, {
              setActive: false
            })
          );
        });

        // verify that the saved active environment is still in the list
        const savedActiveEnvironmentExists =
          environmentsData.find(
            (environmentData) =>
              environmentData.environment.uuid ===
              settings.activeEnvironmentUuid
          ) !== undefined;
        let activeEnvironmentUuid = settings.activeEnvironmentUuid;

        if (savedActiveEnvironmentExists) {
          this.store.update(
            setActiveEnvironmentAction(settings.activeEnvironmentUuid)
          );
        } else if (
          !savedActiveEnvironmentExists &&
          environmentsData.length > 0
        ) {
          this.store.update(
            setActiveEnvironmentAction(environmentsData[0].environment.uuid)
          );

          activeEnvironmentUuid = environmentsData[0].environment.uuid;
        }

        this.store.update(
          updateSettingsAction({
            environments: environmentsData.map((environmentData) => ({
              ...environmentData.environmentDescriptor,
              // update the environment UUID if it changed during migration/UUIDdeduplication
              uuid: environmentData.environment.uuid
            })),
            activeEnvironmentUuid
          })
        );

        if (settings.startEnvironmentsOnLoad) {
          this.toggleAllEnvironments();
        }
      })
    );
  }

  /**
   * Subscribe to initiate saving environments changes.
   * Listen to environments and settings updates, and save environments in each path defined in the settings.
   * Will unwatch files for external change before saving, and rewatch after save is complete
   *
   * @returns
   */
  public saveEnvironments(): Observable<void> {
    return this.store.select('environments').pipe(
      tap(() => {
        // saving flag must be turned on before the debounceTime, otherwise waiting for save to end before closing won't work
        this.storageService.initiateSaving();
      }),
      debounceTime(Config.storageSaveDelay),
      startWith([]),
      // keep previously emitted environments and filter environments that didn't change (pairwise + map)
      pairwise(),
      map(([previousEnvironments, nextEnvironments]) =>
        nextEnvironments.filter(
          (nextEnvironment) =>
            nextEnvironment !==
            previousEnvironments.find(
              (previousEnvironment) =>
                previousEnvironment.uuid === nextEnvironment.uuid
            )
        )
      ),
      tap((modifiedEnvironments) => {
        this.serverService.updateRemoteServerEnvironments(modifiedEnvironments);

        this.mainApiService.send(
          'APP_UPDATE_ENVIRONMENTS',
          modifiedEnvironments
        );
      }),
      withLatestFrom(
        this.store.select('settings').pipe(filter((settings) => !!settings))
      ),
      mergeMap(([environments, settings]) =>
        from(environments).pipe(
          map((environment) => ({
            data: environment,
            descriptor: settings.environments.find(
              (environmentItem) => environmentItem.uuid === environment.uuid
            )
          })),
          filter(
            (environmentInfo) => environmentInfo.descriptor?.path !== undefined
          ),
          mergeMap((environmentInfo) =>
            this.storageService.saveEnvironment(
              environmentInfo.data,
              environmentInfo.descriptor,
              settings.storagePrettyPrint
            )
          )
        )
      )
    );
  }

  /**
   * Ask for confirmation before reloading an environment that was changed externally
   *
   * @param UUID
   * @param environmentPath
   * @returns
   */
  public notifyExternalChange(UUID: string, environmentPath: string) {
    const existingChange = this.environmentChanges$.value.find(
      (environmentChange) => environmentChange.UUID === UUID
    );

    if (!existingChange) {
      this.environmentChanges$.next([
        ...this.environmentChanges$.value,
        {
          UUID,
          environmentPath,
          name: this.store
            .get('environments')
            .find((environment) => environment.uuid === UUID)?.name
        }
      ]);
    }

    // ensure we open the modal only once
    if (!this.environmentChangesNotified) {
      this.environmentChangesNotified = true;

      return this.uiService
        .showConfirmDialog({
          title: 'External changes detected',
          text: 'The following environments were modified outside Mockoon:',
          sub: 'You can disable file monitoring in the application settings (Ctrl + Comma)',
          confirmButtonText: 'Reload all',
          can
... [truncated]
```

### packages/commons-server/src/index.ts
```
export * from './constants/server-messages.constants';
export * from './libs/faker';
export * from './libs/logger';
export * from './libs/server/events-listeners';
export * from './libs/server/server';
export * from './libs/template-parser';
export * from './libs/utils';

```

### packages/app/src/renderer/app/components/environment-databuckets/environment-databuckets.component.ts
```
import { AsyncPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormsModule,
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormGroup
} from '@angular/forms';
import {
  DataBucket,
  DataBucketDefault,
  ProcessedDatabucketWithoutValue
} from '@mockoon/commons';
import { NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { Observable, filter, map, merge, tap } from 'rxjs';
import { EditorComponent } from 'src/renderer/app/components/editor/editor.component';
import { DatabucketsMenuComponent } from 'src/renderer/app/components/menus/databuckets-menu/databuckets-menu.component';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import { FocusOnEventDirective } from 'src/renderer/app/directives/focus-event.directive';
import { FocusableInputs } from 'src/renderer/app/enums/ui.enum';
import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { ServerService } from 'src/renderer/app/services/server.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { Store } from 'src/renderer/app/stores/store';

@Component({
  selector: 'app-environment-databuckets',
  templateUrl: './environment-databuckets.component.html',
  styleUrls: ['./environment-databuckets.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatabucketsMenuComponent,
    FormsModule,
    ReactiveFormsModule,
    FocusOnEventDirective,
    EditorComponent,
    NgbTooltip,
    SvgComponent,
    AsyncPipe
  ]
})
export class EnvironmentDatabucketsComponent {
  private uiService = inject(UIService);
  private store = inject(Store);
  private environmentsService = inject(EnvironmentsService);
  private formBuilder = inject(UntypedFormBuilder);
  private serverService = inject(ServerService);
  private mainApiService = inject(MainApiService);
  public hasDatabuckets$: Observable<boolean>;
  public activeDatabucket$: Observable<DataBucket>;
  public activeDatabucketForm: UntypedFormGroup;
  public focusableInputs = FocusableInputs;
  public bodyEditorConfig$: Observable<any>;
  public processedDatabuckets$: Observable<
    Record<string, ProcessedDatabucketWithoutValue>
  >;
  public scrollToBottom = this.uiService.scrollToBottom;
  public isActiveEnvironmentEditable$ = this.store
    .selectIsActiveEnvironmentEditable()
    .pipe(
      tap((isEditable) => {
        if (isEditable) {
          this.activeDatabucketForm.enable({ emitEvent: false });
        } else {
          this.activeDatabucketForm.disable({ emitEvent: false });
        }
      })
    );

  constructor() {
    this.hasDatabuckets$ = this.store.selectActiveEnvironment().pipe(
      filter((environment) => !!environment),
      map((environment) => environment.data.length > 0)
    );
    this.activeDatabucket$ = this.store.selectActiveDatabucket();
    this.processedDatabuckets$ =
      this.store.selectActiveEnvironmentProcessedDatabuckets();
    this.bodyEditorConfig$ = this.store.select('bodyEditorConfig');

    this.activeDatabucketForm = this.formBuilder.group({
      name: [DataBucketDefault.name],
      documentation: [DataBucketDefault.documentation],
      value: [DataBucketDefault.value]
    });

    // send new activeDatabucketForm values to the store, one by one
    merge(
      ...Object.keys(this.activeDatabucketForm.controls).map((controlName) =>
        this.activeDatabucketForm
          .get(controlName)
          .valueChanges.pipe(map((newValue) => ({ [controlName]: newValue })))
      )
    )
      .pipe(
        tap((newProperty) => {
          this.environmentsService.updateActiveDatabucket(newProperty);
        }),
        takeUntilDestroyed()
      )
      .subscribe();

    // subscribe to active route changes to reset the form
    this.activeDatabucket$
      .pipe(
        filter((databucket) => !!databucket),
        this.store.distinctUUIDOrForce(),
        takeUntilDestroyed()
      )
      .subscribe((activeDatabucket) => {
        this.activeDatabucketForm.patchValue(
          {
            name: activeDatabucket.name,
            documentation: activeDatabucket.documentation,
            value: activeDatabucket.value
          },
          { emitEvent: false }
        );
      });
  }

  public copyToClipboard(databucketId: string) {
    this.mainApiService.send('APP_WRITE_CLIPBOARD', databucketId);
  }

  public showDatabucketValue(
    databucketUuid: string,
    validJson: boolean,
    databucketName: string
  ) {
    const activeEnvironmentUuid = this.store.get('activeEnvironmentUUID');

    this.serverService
      .getProcessedDatabucketValue(activeEnvironmentUuid, databucketUuid)
      .subscribe((d) => {
        this.uiService.openModal('editor', {
          title: `"${databucketName}" databucket value`,
          subtitle:
            'This is the current in-memory value of the processed databucket content',
          text: validJson ? JSON.stringify(d, null, 2) : d
        });
      });
  }
}

```

### packages/app/src/renderer/app/components/header/header.component.ts
```
import { AsyncPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject
} from '@angular/core';
import { User } from '@mockoon/cloud';
import { Environment } from '@mockoon/commons';
import {
  NgbDropdown,
  NgbDropdownMenu,
  NgbDropdownToggle,
  NgbPopover,
  NgbTooltip
} from '@ng-bootstrap/ng-bootstrap';
import { EMPTY, Observable, forkJoin, from } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import { TeamPresenceComponent } from 'src/renderer/app/components/team-presence/team-presence.component';
import { TourStepDirective } from 'src/renderer/app/directives/tour-step.directive';
import { EnvironmentLog } from 'src/renderer/app/models/environment-logs.model';
import {
  EnvironmentStatus,
  ViewsNameType
} from 'src/renderer/app/models/store.model';
import { DeployService } from 'src/renderer/app/services/deploy.service';
import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { RemoteConfigService } from 'src/renderer/app/services/remote-config.service';
import { SyncService } from 'src/renderer/app/services/sync.service';
import { ToastsService } from 'src/renderer/app/services/toasts.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { UserService } from 'src/renderer/app/services/user.service';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';
import { environment as env } from 'src/renderer/environments/environment';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgbPopover,
    TourStepDirective,
    NgbTooltip,
    SvgComponent,
    TeamPresenceComponent,
    NgbDropdown,
    NgbDropdownToggle,
    NgbDropdownMenu,
    AsyncPipe
  ]
})
export class HeaderComponent implements OnInit {
  private store = inject(Store);
  private environmentsService = inject(EnvironmentsService);
  private userService = inject(UserService);
  private remoteConfigService = inject(RemoteConfigService);
  private uiService = inject(UIService);
  private syncService = inject(SyncService);
  private toastsService = inject(ToastsService);
  private deployService = inject(DeployService);
  private mainApiService = inject(MainApiService);

  public activeEnvironment$: Observable<Environment>;
  public user$: Observable<User>;
  public activeView$: Observable<ViewsNameType>;
  public activeEnvironmentState$: Observable<EnvironmentStatus>;
  public environmentLogs$: Observable<EnvironmentLog[]>;
  public os$: Observable<string>;
  public sync$ = this.store.select('sync');
  public tabs: {
    id: ViewsNameType;
    title: string;
    icon: string;
    count$?: Observable<number>;
  }[];
  public planLabels = {
    FREE: 'Free',
    SOLO: 'Solo',
    TEAM: 'Team',
    ENTERPRISE: 'Enterprise'
  };
  public tourIds = {
    ENV_LOGS: 'tour-environment-logs',
    ENV_PROXY: 'tour-environment-proxy'
  };
  public isDev = !env.production;
  public isWeb = Config.isWeb;
  public accountUrl = Config.accountUrl;

  ngOnInit() {
    this.os$ = from(this.mainApiService.invoke('APP_GET_OS'));
    this.user$ = this.store.select('user');
    this.activeView$ = this.store.select('activeView');
    this.activeEnvironment$ = this.store.selectActiveEnvironment();
    this.activeEnvironmentState$ = this.store.selectActiveEnvironmentStatus();
    this.environmentLogs$ = this.store.selectActiveEnvironmentLogs();

    this.tabs = [
      {
        id: 'ENV_ROUTES',
        title: 'Routes',
        icon: 'endpoints',
        count$: this.activeEnvironment$.pipe(
          map((environment) => (environment ? environment.routes.length : null))
        )
      },
      {
        id: 'ENV_DATABUCKETS',
        title: 'Data',
        icon: 'data',
        count$: this.activeEnvironment$.pipe(
          map((environment) => (environment ? environment.data.length : null))
        )
      },
      {
        id: 'ENV_HEADERS',
        title: 'Headers',
        icon: 'featured_play_list',
        count$: this.activeEnvironment$.pipe(
          map((environment) =>
            environment ? environment.headers.length : null
          )
        )
      },
      {
        id: 'ENV_CALLBACKS',
        title: 'Callbacks',
        icon: 'call_made',
        count$: this.activeEnvironment$.pipe(
          map((environment) =>
            environment ? environment.callbacks.length : null
          )
        )
      },
      {
        id: 'ENV_LOGS',
        title: 'Logs',
        icon: 'history',
        count$: this.environmentLogs$.pipe(
          map((environmentLogs) =>
            environmentLogs ? environmentLogs.length : null
          )
        )
      },
      {
        id: 'ENV_PROXY',
        title: 'Proxy',
        icon: 'security'
      },
      { id: 'ENV_SETTINGS', title: 'Settings', icon: 'settings' }
    ];
  }

  /**
   * Set the application active view (routes / logs / settings)
   */
  public setActiveView(viewName: ViewsNameType) {
    this.environmentsService.setActiveView(viewName);
  }

  /**
   * Toggle active environment running state (start/stop)
   */
  public toggleEnvironment(
    environmentUuid: string,
    environmentStatus: EnvironmentStatus
  ) {
    if (this.isWeb) {
      // quick re-deploy
      if (environmentStatus.needRestart) {
        this.deployService.quickRedeploy(environmentUuid).subscribe();
      } else {
        this.uiService.openModal('deploy', environmentUuid);
      }
    } else {
      this.environmentsService.toggleEnvironment();
    }
  }

  public openSettings() {
    this.uiService.openModal('settings');
  }

  public login() {
    this.userService.startLoginFlow();
  }

  /**
   * Logout the user
   */
  public logout() {
    this.userService.logout().subscribe();
  }

  /**
   * Refresh the user account information
   */
  public refreshAccount() {
    forkJoin([
      this.userService.getUserInfo(true),
      this.remoteConfigService.fetchConfig()
    ])
      .pipe(
        switchMap(() => this.deployService.getInstances(true)),
        catchError(() => EMPTY)
      )
      .subscribe(() => {
        this.toastsService.addToast('success', 'Account information refreshed');
      });
  }

  public disconnectSync() {
    this.syncService.disconnect();
  }

  public refreshAuthToken() {
    this.userService.getIdToken(true).subscribe();
  }

  /**
   * Open the command palette
   */
  public openCommandPalette() {
    this.uiService.openModal('commandPalette');
  }
}

```

### packages/app/src/renderer/app/components/environment-routes/environment-routes.component.ts
```
import { AsyncPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormsModule,
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormGroup
} from '@angular/forms';
import { DeployInstance } from '@mockoon/cloud';
import {
  Environment,
  FileExtensionsWithTemplating,
  GetContentType,
  GetRouteResponseContentType,
  Header,
  INDENT_SIZE,
  Methods,
  MimeTypesWithTemplating,
  ParsedJSONBodyMimeTypes,
  ReorderAction,
  ReorderableContainers,
  ResponseMode,
  Route,
  RouteDefault,
  RouteResponse,
  RouteResponseDefault,
  RouteType,
  RulesDisablingResponseModes,
  RulesNotUsingDefaultResponse,
  StreamingMode,
  express5PathConvert,
  pathMatch,
  pathMatchErrorBuilder,
  stringIncludesArrayItems
} from '@mockoon/commons';
import {
  NgbDropdown,
  NgbDropdownItem,
  NgbDropdownMenu,
  NgbDropdownToggle,
  NgbPopover,
  NgbTooltip
} from '@ng-bootstrap/ng-bootstrap';
import { Observable, combineLatest, from, merge } from 'rxjs';
import {
  combineLatestWith,
  distinctUntilChanged,
  filter,
  map,
  mergeMap,
  startWith,
  tap
} from 'rxjs/operators';
import { TimedBoolean } from 'src/renderer/app/classes/timed-boolean';
import { CustomSelectComponent } from 'src/renderer/app/components/custom-select/custom-select.component';
import {
  DropdownMenuComponent,
  DropdownMenuItem
} from 'src/renderer/app/components/dropdown-menu/dropdown-menu.component';
import { EditorComponent } from 'src/renderer/app/components/editor/editor.component';
import { FilterComponent } from 'src/renderer/app/components/filter/filter.component';
import { HeadersListComponent } from 'src/renderer/app/components/headers-list/headers-list.component';
import { RoutesMenuComponent } from 'src/renderer/app/components/menus/routes-menu/routes-menu.component';
import { RouteCallbacksComponent } from 'src/renderer/app/components/route-callbacks/route-callbacks.component';
import { RouteResponseRulesComponent } from 'src/renderer/app/components/route-response-rules/route-response-rules.component';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import { ToggleComponent } from 'src/renderer/app/components/toggle/toggle.component';
import { statusCodeValidation } from 'src/renderer/app/constants/masks.constants';
import {
  StatusCodes,
  defaultContentType
} from 'src/renderer/app/constants/routes.constants';
import { Texts } from 'src/renderer/app/constants/texts.constant';
import { DraggableDirective } from 'src/renderer/app/directives/draggable.directive';
import { DropzoneDirective } from 'src/renderer/app/directives/dropzone.directive';
import { FocusOnEventDirective } from 'src/renderer/app/directives/focus-event.directive';
import { InputNumberDirective } from 'src/renderer/app/directives/input-number.directive';
import { TourStepDirective } from 'src/renderer/app/directives/tour-step.directive';
import { ValidPathDirective } from 'src/renderer/app/directives/valid-path.directive';
import { FocusableInputs } from 'src/renderer/app/enums/ui.enum';
import {
  buildFullPath,
  buildResponseLabel,
  textFilter
} from 'src/renderer/app/libs/utils.lib';
import {
  DropdownItems,
  ToggleItems
} from 'src/renderer/app/models/common.model';
import { EnvironmentLog } from 'src/renderer/app/models/environment-logs.model';
import {
  EnvironmentsStatuses,
  TabsNameType
} from 'src/renderer/app/models/store.model';
import { DialogsService } from 'src/renderer/app/services/dialogs.service';
import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';

type fileDropdownMenuPayload = { filePath: string; environmentUuid: string };

@Component({
  selector: 'app-environment-routes',
  templateUrl: './environment-routes.component.html',
  styleUrls: ['./environment-routes.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RoutesMenuComponent,
    NgbPopover,
    TourStepDirective,
    FormsModule,
    ReactiveFormsModule,
    CustomSelectComponent,
    ValidPathDirective,
    FocusOnEventDirective,
    NgbTooltip,
    SvgComponent,
    ToggleComponent,
    InputNumberDirective,
    NgbDropdown,
    NgbDropdownToggle,
    NgbDropdownMenu,
    FilterComponent,
    NgbDropdownItem,
    DraggableDirective,
    DropzoneDirective,
    EditorComponent,
    DropdownMenuComponent,
    HeadersListComponent,
    RouteResponseRulesComponent,
    RouteCallbacksComponent,
    AsyncPipe
  ]
})
export class EnvironmentRoutesComponent {
  private uiService = inject(UIService);
  private store = inject(Store);
  private formBuilder = inject(UntypedFormBuilder);
  private dialogsService = inject(DialogsService);
  private environmentsService = inject(EnvironmentsService);
  private mainApiService = inject(MainApiService);

  public activeEnvironment$: Observable<Environment>;
  public activeRoute$: Observable<Route>;
  public activeRouteResponse$: Observable<RouteResponse>;
  public activeRouteResponses$: Observable<
    (RouteResponse & { originalIndex: number })[]
  >;
  public activeRouteResponseIndex$: Observable<number>;
  public activeRouteResponseLastLog$: Observable<EnvironmentLog>;
  public activeResponseFileMimeType$: Observable<{
    mimeType: string;
    supportsTemplating: boolean;
  }>;
  public buildResponseLabel = buildResponseLabel;
  public effectiveContentType$: Observable<string>;
  public defaultResponseTooltip$: Observable<string>;
  public routeHasErrors$: Observable<string>;
  public environmentsStatus$: Observable<EnvironmentsStatuses>;
  public activeTab$: Observable<TabsNameType>;
  public deleteCurrentRouteResponseRequested$ = new TimedBoolean();
  public bodyEditorConfig$: Observable<any>;
  public activeRouteForm: UntypedFormGroup;
  public activeRouteResponseForm: UntypedFormGroup;
  public scrollToBottom = this.uiService.scrollToBottom;
  public databuckets$: Observable<DropdownItems>;
  public externalLink$: Observable<string>;
  public methods: DropdownItems = [
    {
      value: Methods.all,
      label: 'All methods',
      classes: 'color-method-all'
    },
    {
      value: Methods.get,
      label: 'GET',
      classes: 'color-method-get'
    },
    {
      value: Methods.post,
      label: 'POST',
      classes: 'color-method-post'
    },
    {
      value: Methods.put,
      label: 'PUT',
      classes: 'color-method-put'
    },
    {
      value: Methods.patch,
      label: 'PATCH',
      classes: 'color-method-patch'
    },
    {
      value: Methods.delete,
      label: 'DELETE',
      classes: 'color-method-delete'
    },
    {
      value: Methods.head,
      label: 'HEAD',
      classes: 'color-method-head'
    },
    {
      value: Methods.options,
      label: 'OPTIONS',
      classes: 'color-method-options'
    },
    {
      value: Methods.propfind,
      label: 'PROPFIND',
      classes: 'color-method-propfind'
    },
    {
      value: Methods.proppatch,
      label: 'PROPPATCH',
      classes: 'color-method-proppatch'
    },
    {
      value: Methods.move,
      label: 'MOVE',
      classes: 'color-method-move'
    },
    {
      value: Methods.copy,
      label: 'COPY',
      classes: 'color-method-copy'
    },
    {
      value: Methods.mkcol,
      label: 'MKCOL',
      classes: 'color-method-mkcol'
    },
    {
      value: Methods.lock,
      label: 'LOCK',
      classes: 'color-method-lock'
    },
    {
      value: Methods.unlock,
      label: 'UNLOCK',
      classes: 'color-method-unlock'
    }
  ];
  public responseModes: ToggleItems = [
    {
      value: ResponseMode.RANDOM,
      icon: 'shuffle',
      tooltip: 'Random response mode (will disable the rules)'
    },
    {
      value: ResponseMode.SEQUENTIAL,
      icon: 'repeat',
      tooltip: 'Sequential response mode (will disable the rules)'
    },
    {
      value: ResponseMode.DISABLE_RULES,
      icon: 'rule',
      tooltip: 'Disabled rules mode (default response only)',
      activeClass: 'text-warning'
    },
    {
      value: ResponseMode.FALLBACK,
      icon: 'low_priority',
      tooltip:
        'Fallback response mode (does not return the default response if none of the rules match, will jump to the next route or use the proxy if configured)'
    }
  ];
  // disables fallback mode for websockets.
  public responseModesForWs: ToggleItems = this.responseModes.filter(
    (m) => m.value !== ResponseMode.FALLBACK
  );
  public streamingModes: ToggleItems = [
    {
      value: StreamingMode.UNICAST,
      icon: 'events',
      tooltip: 'One-to-one streaming'
    },
    {
      value: StreamingMode.BROADCAST,
      icon: 'broadcast',
      tooltip: 'Broadcast streaming'
    }
  ];
  public bodyType$: Observable<ToggleItems> = this.store
    .selectIsActiveEnvCloud()
    .pipe(
      map((isEnvCloud) => [
        {
          value: 'INLINE',
          label: 'Inline'
        },
        ...(isEnvCloud
          ? []
          : [
              {
                value: 'FILE',
                label: 'File'
              }
            ]),
        {
          value: 'DATABUCKET',
          label: 'Data'
        }
      ])
    );
  public window = window;
  public rulesDisablingResponseModes: ResponseMode[] =
    RulesDisablingResponseModes;
  public rulesNotUsingDefaultResponse: ResponseMode[] =
    RulesNotUsingDefaultResponse;
  public statusCodes = StatusCodes;
  public statusCodeValidation = statusCodeValidation;
  public focusableInputs = FocusableInputs;
  public Infinity = Infinity;
  public texts = Texts;
  public fileDropdownMenuItems: DropdownMenuItem[] = [
    {
      label: 'Browse',
      icon: 'find_in_page',
      twoSteps: false,
      action: () => {
        this.dialogsService
          .showOpenDialog('Choose a file', null, false)
          .pipe(
            tap((filePaths) => {
              if (filePaths?.[0]) {
                this.activeRouteResponseForm
                  .get('filePath')
                  .setValue(filePaths[0]);
              }
            })
          )
          .subscribe();
      },
      disabled$: () =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable))
    },
    {
      label: 'Show file in explorer/finder',
      icon: 'folder',
      twoSteps: false,
      action: ({ environmentUuid, filePath }: fileDropdownMenuPayload) => {
        const environmentPath = this.store.getEnvironmentPath(environmentUuid);

        this.mainApiService.send('APP_SHOW_FILE', filePath, environmentPath);
      }
    },
    {
      label: 'Open file in editor',
      icon: 'file_open',
      twoSteps: false,
      action: ({ environmentUuid, filePath }: fileDropdownMenuPayload) => {
        const environmentPath = this.store.getEnvironmentPath(environmentUuid);

        this.mainApiService.send('APP_OPEN_FILE', filePath, environmentPath);
      }
    }
  ];
  public isActiveEnvironmentEditable$ = this.store
    .selectIsActiveEnvironmentEditable()
    .pipe(
      tap((isEditable) => {
        if (isEditable) {
          this.activeRouteForm.enable({ emitEvent: false });
          this.activeRouteResponseForm.enable({ emitEvent: false });
          this.refreshDisabledFields();
        } else {
          this.activeRouteForm.disable({ emitEvent: false });
          this.activeRouteResponseForm.disable({ emitEvent: false });
        }
      })
    );

  constructor() {
    this.activeEnvironment$ = this.store.selectActiveEnvironment().pipe(
      filter((activeEnvironment) => !!activeEnvironment),
      distinctUntilChanged()
    );
    this.activeRoute$ = this.store.selectActiveRoute();
    this.activeRouteResponses$ = this.activeRoute$.pipe(
     
... [truncated]
```

### packages/app/src/renderer/app/components/footer/footer.component.ts
```
import { AsyncPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  Input,
  OnInit,
  inject
} from '@angular/core';
import { Plans } from '@mockoon/cloud';
import { NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { BehaviorSubject, Observable, from, map } from 'rxjs';
import { SpinnerComponent } from 'src/renderer/app/components/spinner.component';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import {
  TemplatesTabsName,
  UIState
} from 'src/renderer/app/models/store.model';
import { EventsService } from 'src/renderer/app/services/events.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { TemplatesService } from 'src/renderer/app/services/templates.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { setActiveTemplatesTabAction } from 'src/renderer/app/stores/actions';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgbTooltip, SvgComponent, AsyncPipe, SpinnerComponent]
})
export class FooterComponent implements OnInit {
  private store = inject(Store);
  private eventsService = inject(EventsService);
  private uiService = inject(UIService);
  private templateService = inject(TemplatesService);
  private mainApiService = inject(MainApiService);

  @Input() public isTemplateModalOpen: boolean;
  @Input() public isTemplateLoading: boolean;
  public updateAvailable$: BehaviorSubject<string | null>;
  public platform$ = from(this.mainApiService.invoke('APP_GET_OS'));
  public uiState$: Observable<UIState>;
  public generatingTemplate$ = this.templateService.generatingTemplate$;
  public generatingEndpoint$ = this.templateService.generatingEndpoint$;
  public releaseUrl = Config.releasePublicURL;
  public showFeedback$ = this.store
    .select('user')
    .pipe(map((user) => !!user && user.plan !== Plans.FREE));
  public version = Config.appVersion;

  ngOnInit() {
    this.updateAvailable$ = this.eventsService.updateAvailable$;
    this.uiState$ = this.store.select('uiState');
  }

  /**
   * Apply the update
   */
  public applyUpdate() {
    this.mainApiService.send('APP_APPLY_UPDATE');
  }

  public openTemplateModal(tab: TemplatesTabsName) {
    this.store.update(setActiveTemplatesTabAction(tab));
    this.uiService.openModal('templates');
  }

  public openFeedbackModal() {
    this.uiService.openModal('feedback');
  }

  public openChangelogModal() {
    this.uiService.openModal('changelog');
  }
}

```

### packages/app/src/renderer/app/components/filter/filter.component.ts
```
import { AsyncPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  inject,
  input
} from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import {
  FormsModule,
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormControl
} from '@angular/forms';
import { NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { Observable, debounceTime, from, switchMap, tap } from 'rxjs';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import { FocusOnEventDirective } from 'src/renderer/app/directives/focus-event.directive';
import { FocusableInputs } from 'src/renderer/app/enums/ui.enum';
import { StoreType } from 'src/renderer/app/models/store.model';
import { EventsService } from 'src/renderer/app/services/events.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { updateFilterAction } from 'src/renderer/app/stores/actions';
import { Store } from 'src/renderer/app/stores/store';

@Component({
  selector: 'app-filter',
  templateUrl: 'filter.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    FocusOnEventDirective,
    NgbTooltip,
    SvgComponent,
    AsyncPipe
  ]
})
export class FilterComponent {
  private store = inject(Store);
  private formBuilder = inject(UntypedFormBuilder);
  private eventsService = inject(EventsService);
  private uiService = inject(UIService);
  private mainApiService = inject(MainApiService);
  public readonly filterName = input.required<keyof StoreType['filters']>();
  public readonly focusableInput = input.required<FocusableInputs>();
  public filter: UntypedFormControl;
  public os: string;
  public os$: Observable<string>;

  @HostListener('keydown', ['$event'])
  public escapeFilterInput(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      this.clearFilter();
    }
  }

  @HostListener('document:keydown', ['$event'])
  public focusFilterInput(event: KeyboardEvent) {
    if (
      ((event.ctrlKey && this.os !== 'darwin') ||
        (event.metaKey && this.os === 'darwin')) &&
      event.shiftKey &&
      event.key.toLowerCase() === 'f'
    ) {
      if (this.uiService.getModalInstance('templates')) {
        this.eventsService.focusInput.next(FocusableInputs.TEMPLATES_FILTER);
      } else if (this.store.get('activeView') === 'ENV_ROUTES') {
        this.eventsService.focusInput.next(FocusableInputs.ROUTE_FILTER);
      } else if (this.store.get('activeView') === 'ENV_DATABUCKETS') {
        this.eventsService.focusInput.next(FocusableInputs.DATABUCKET_FILTER);
      } else if (this.store.get('activeView') === 'ENV_CALLBACKS') {
        this.eventsService.focusInput.next(FocusableInputs.CALLBACK_FILTER);
      } else if (this.store.get('activeView') === 'ENV_LOGS') {
        this.eventsService.focusInput.next(FocusableInputs.LOGS_FILTER);
      }
    }
  }

  constructor() {
    this.os$ = from(this.mainApiService.invoke('APP_GET_OS')).pipe(
      tap((os) => {
        this.os = os;
      })
    );
    this.filter = this.formBuilder.control('');
    this.filter.valueChanges
      .pipe(
        debounceTime(10),
        tap((search) =>
          this.store.update(updateFilterAction(this.filterName(), search))
        ),
        takeUntilDestroyed()
      )
      .subscribe();

    toObservable(this.filterName)
      .pipe(
        switchMap((filter) => this.store.selectFilter(filter)),
        tap((search) => {
          this.filter.patchValue(search, { emitEvent: false });
        }),
        takeUntilDestroyed()
      )
      .subscribe();
  }

  public clearFilter() {
    this.store.update(updateFilterAction(this.filterName(), ''));
  }
}

```

### packages/app/src/renderer/app/components/menus/routes-menu/routes-menu.component.ts
```
import { AsyncPipe, NgTemplateOutlet, UpperCasePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  inject,
  viewChild,
  viewChildren
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormsModule,
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormGroup
} from '@angular/forms';
import { DeployInstance } from '@mockoon/cloud';
import {
  Environment,
  Environments,
  Folder,
  FolderChild,
  ReorderAction,
  ReorderableContainers,
  ResponseMode,
  Route
} from '@mockoon/commons';
import {
  NgbDropdown,
  NgbDropdownMenu,
  NgbDropdownToggle,
  NgbPopover,
  NgbTooltip
} from '@ng-bootstrap/ng-bootstrap';
import { BehaviorSubject, Observable, combineLatest, merge } from 'rxjs';
import {
  debounceTime,
  distinctUntilChanged,
  filter,
  map,
  tap,
  withLatestFrom
} from 'rxjs/operators';
import { ActionToolbarComponent } from 'src/renderer/app/components/action-toolbar/action-toolbar.component';
import {
  DropdownMenuComponent,
  DropdownMenuItem
} from 'src/renderer/app/components/dropdown-menu/dropdown-menu.component';
import { EditableElementComponent } from 'src/renderer/app/components/editable-element/editable-element.component';
import { FilterComponent } from 'src/renderer/app/components/filter/filter.component';
import { SvgComponent } from 'src/renderer/app/components/svg/svg.component';
import { DraggableDirective } from 'src/renderer/app/directives/draggable.directive';
import { DropzoneDirective } from 'src/renderer/app/directives/dropzone.directive';
import { ResizeColumnDirective } from 'src/renderer/app/directives/resize-column.directive';
import { ScrollWhenActiveDirective } from 'src/renderer/app/directives/scroll-to-active.directive';
import { TourStepDirective } from 'src/renderer/app/directives/tour-step.directive';
import { FocusableInputs } from 'src/renderer/app/enums/ui.enum';
import {
  buildFullPath,
  buildSelectionRange,
  getVisibleOrderedDatasetUuids,
  textFilter,
  toggleSelectionUuid
} from 'src/renderer/app/libs/utils.lib';
import {
  DuplicatedRoutesTypes,
  EnvironmentsStatuses
} from 'src/renderer/app/models/store.model';
import { ToolbarButtonConfig } from 'src/renderer/app/models/ui.model';
import { EnvironmentsService } from 'src/renderer/app/services/environments.service';
import { MainApiService } from 'src/renderer/app/services/main-api.service';
import { UIService } from 'src/renderer/app/services/ui.service';
import { Store } from 'src/renderer/app/stores/store';
import { Config } from 'src/renderer/config';
import { Settings } from 'src/shared/models/settings.model';

type FullFolder = {
  uuid: string;
  name: string;
  children: (
    | { type: 'folder'; data: Folder }
    // routes has an extra property isHidden$ that is an observable of the route visibility based on the search filter (thus we avoid using a function in the template)
    | { type: 'route'; isHidden$: Observable<boolean>; data: Route }
  )[];
};

type routeDropdownMenuPayload = { parentId: string; routeUuid: string };
type folderDropdownMenuPayload = { folder: Folder; folderUuid: string };

@Component({
  selector: 'app-routes-menu',
  templateUrl: './routes-menu.component.html',
  styleUrls: ['./routes-menu.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgbPopover,
    TourStepDirective,
    NgbDropdown,
    NgbDropdownToggle,
    SvgComponent,
    NgbDropdownMenu,
    FilterComponent,
    NgTemplateOutlet,
    ResizeColumnDirective,
    DraggableDirective,
    DropzoneDirective,
    ScrollWhenActiveDirective,
    FormsModule,
    ReactiveFormsModule,
    EditableElementComponent,
    DropdownMenuComponent,
    ActionToolbarComponent,
    NgbTooltip,
    AsyncPipe,
    UpperCasePipe
  ]
})
export class RoutesMenuComponent {
  private environmentsService = inject(EnvironmentsService);
  private store = inject(Store);
  private uiService = inject(UIService);
  private formBuilder = inject(UntypedFormBuilder);
  private mainApiService = inject(MainApiService);
  private routesMenu = viewChild<ElementRef<HTMLUListElement>>('routesMenu');
  private routeRows = viewChildren<ElementRef<HTMLAnchorElement>>('routeRow');
  public settings$: Observable<Settings>;
  public activeEnvironment$: Observable<Environment>;
  public isActiveEnvironmentCloud$ = this.store.selectIsActiveEnvCloud();
  public environments$: Observable<Environments> =
    this.store.select('environments');
  public rootFolder$: Observable<FullFolder>;
  public activeRoute$: Observable<Route>;
  public environmentsStatus$: Observable<EnvironmentsStatuses>;
  public duplicatedRoutes$: Observable<DuplicatedRoutesTypes>;
  public disabledRoutes$: Observable<string[]>;
  public collapsedFolders$: Observable<string[]>;
  public routesFilter$: Observable<string>;
  public isActiveEnvironmentEditable$ =
    this.store.selectIsActiveEnvironmentEditable();
  private manualDragEnabled$ = new BehaviorSubject(true);
  public dragEnabled$ = combineLatest([
    this.isActiveEnvironmentEditable$,
    this.manualDragEnabled$
  ]).pipe(
    map(([isEditable, manualDragEnabled]) => isEditable && manualDragEnabled)
  );
  public focusableInputs = FocusableInputs;
  public folderForm: UntypedFormGroup;
  public menuSize = Config.defaultSecondaryMenuSize;
  public draggedFolderCollapsed: boolean;
  public ResponseMode = ResponseMode;
  public isWeb = Config.isWeb;
  // Multi-selection state for batch actions (local UI state).
  // A route is "selected" when present in this set; it is independent of the
  // "active" route
  public selectedRoutes$ = new BehaviorSubject<string[]>([]);
  // Tracks the selection anchor used for shift-range selection support.
  private lastClickedRouteUuid: string | null = null;
  // Map of routeUuid -> parentId (folder uuid or 'root'), used by batch duplicate.
  private routeParentMap = new Map<string, string>();
  public routeDropdownMenuItems: DropdownMenuItem[] = [
    {
      label: 'Duplicate',
      icon: 'content_copy',
      twoSteps: false,
      disabled$: () =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable)),
      action: ({ parentId, routeUuid }: routeDropdownMenuPayload) => {
        this.environmentsService.duplicateRoute(parentId, routeUuid);
      }
    },
    {
      label: 'Duplicate to environment',
      icon: 'input',
      twoSteps: false,
      disabled$: () =>
        this.environments$.pipe(map((environments) => environments.length < 2)),
      action: ({ routeUuid }: routeDropdownMenuPayload) => {
        this.environmentsService.startEntityDuplicationToAnotherEnvironment(
          'route',
          [routeUuid]
        );
      }
    },
    {
      label: "Copy configuration to clipboard (Mockoon's JSON format)",
      icon: 'assignment',
      twoSteps: false,
      action: ({ routeUuid }: routeDropdownMenuPayload) => {
        this.environmentsService.copyRouteToClipboard(routeUuid);
      }
    },
    {
      label: 'Copy full path to clipboard',
      icon: 'assignment',
      twoSteps: false,
      action: ({ routeUuid }: routeDropdownMenuPayload) => {
        const activeEnvironment = this.store.getActiveEnvironment();
        const route = this.store.getRouteByUUID(routeUuid);

        let activeInstance: DeployInstance;

        if (this.isWeb) {
          activeInstance = this.store
            .get('deployInstances')
            .find(
              (instance) => instance.environmentUuid === activeEnvironment.uuid
            );
        }

        this.mainApiService.send(
          'APP_WRITE_CLIPBOARD',
          buildFullPath(activeEnvironment, route, activeInstance)
        );
      }
    },
    ...(this.isWeb
      ? []
      : [
          {
            label: 'Toggle',
            icon: 'power_settings_new',
            twoSteps: false,
            action: ({ routeUuid }: routeDropdownMenuPayload) => {
              this.environmentsService.toggleRoute(routeUuid);
            }
          }
        ]),
    {
      label: 'Delete',
      icon: 'delete',
      confirmIcon: 'error',
      confirmLabel: 'Confirm deletion',
      twoSteps: true,
      disabled$: () =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable)),
      action: ({ routeUuid }: routeDropdownMenuPayload) => {
        this.environmentsService.removeRoute(routeUuid);
      }
    }
  ];

  public getToolbarButtons(): ToolbarButtonConfig[] {
    const disabled$ = this.isActiveEnvironmentEditable$.pipe(
      map((isEditable) => !isEditable)
    );

    const buttons: ToolbarButtonConfig[] = [
      {
        id: 'routes-batch-duplicate',
        action: 'duplicate',
        icon: 'content_copy',
        ariaLabel: 'Duplicate selected routes',
        tooltip: 'Duplicate selected routes',
        disabled$
      },
      {
        id: 'routes-batch-duplicate-to-env',
        action: 'duplicate-to-env',
        icon: 'input',
        ariaLabel: 'Duplicate selected routes to another environment',
        tooltip: 'Duplicate selected routes to another environment'
      }
    ];

    if (!this.isWeb) {
      buttons.push({
        id: 'routes-batch-toggle',
        action: 'toggle',
        icon: 'power_settings_new',
        ariaLabel: 'Toggle selected routes',
        tooltip: 'Toggle selected routes (enable/disable)'
      });
    }

    buttons.push(
      {
        id: 'routes-batch-delete',
        action: 'delete',
        icon: 'delete',
        ariaLabel: 'Delete selected routes',
        tooltip: 'Delete selected routes',
        twoSteps: true,
        confirmIcon: 'error',
        confirmAriaLabel: 'Confirm delete selected routes',
        confirmTooltip: 'Click again to confirm deletion',
        disabled$
      },
      {
        id: 'routes-batch-clear',
        action: 'clear',
        icon: 'close',
        ariaLabel: 'Clear selection',
        tooltip: 'Clear selection (Esc)'
      }
    );

    return buttons;
  }
  public folderDropdownMenuItems: DropdownMenuItem[] = [
    {
      label: 'Add CRUD route',
      icon: 'endpoints',
      twoSteps: false,
      disabled$: () =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable)),
      action: ({ folderUuid }: folderDropdownMenuPayload) => {
        this.environmentsService.addCRUDRoute(folderUuid);
      }
    },
    {
      label: 'Add HTTP route',
      icon: 'endpoint',
      twoSteps: false,
      disabled$: () =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable)),
      action: ({ folderUuid }: folderDropdownMenuPayload) => {
        this.environmentsService.addHTTPRoute(folderUuid);
      }
    },
    {
      label: 'Add folder',
      icon: 'folder',
      twoSteps: false,
      disabled$: () =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable)),
      action: ({ folderUuid }: folderDropdownMenuPayload) => {
        this.environmentsService.addFolder(folderUuid);
      }
    },
    ...(this.isWeb
      ? []
      : [
          {
            label: 'Toggle direct child routes',
            icon: 'power_settings_new',
            twoSteps: false,
            action: ({ folderUuid }: folderDropdownMenuPayload) => {
              this.environmentsService.toggleFolder(folderUuid);
            }
          }
        ]),
    {
      label: 'Delete folder',
      icon: 'delete',
      twoSteps: true,
      confirmIcon: 'error',
      confirmLabel: 'Confirm deletion',
      disabled$: ({ folder }: folderDropdownMenuPayload) =>
        this.store
          .selectIsActiveEnvironmentEditable()
          .pipe(map((isEditable) => !isEditable || folder.children.length > 0)),
      disabledLabel$: () =>
        this.store
          .selectIsActiveEn
... [truncated]
```

(+71 more files reference the changed code)
Repository Map
packages/app/src/main/libs/auth.ts
packages/app/src/main/libs/custom-protocol.ts
packages/app/src/main/libs/hot-reload.ts
packages/app/src/main/libs/ipc.ts
packages/app/src/main/libs/logs.ts
packages/app/src/main/libs/main-window.ts
packages/app/src/main/libs/menu.ts
packages/app/src/main/libs/paths.ts
packages/app/src/main/libs/runtime-args.ts
packages/app/src/main/libs/server-management.ts
packages/app/src/main/libs/settings.ts
packages/app/src/main/libs/storage.ts
packages/app/src/main/libs/update.ts
packages/app/src/main/libs/watch-file.ts
packages/app/src/main/libs/zoom.ts
packages/app/src/renderer/app/components/dropdown-menu/dropdown-menu.component.ts
packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts
packages/app/src/renderer/app/models/app-environment.model.ts
packages/app/src/renderer/app/models/callback.model.ts
packages/app/src/renderer/app/models/command-palette.model.ts
packages/app/src/renderer/app/models/common.model.ts
packages/app/src/renderer/app/models/data.model.ts
packages/app/src/renderer/app/models/editor.model.ts
packages/app/src/renderer/app/models/environment-logs.model.ts
packages/app/src/renderer/app/models/main-api.model.ts
packages/app/src/renderer/app/models/messages.model.ts
packages/app/src/renderer/app/models/openapi.model.ts
packages/app/src/renderer/app/models/store.model.ts
packages/app/src/renderer/app/models/toasts.model.ts
packages/app/src/renderer/app/models/tour.model.ts
packages/app/src/renderer/app/models/ui.model.ts
packages/app/src/renderer/app/services/app-quit.services.ts
packages/app/src/renderer/app/services/command-palette.service.ts
packages/app/src/renderer/app/services/data.service.ts
packages/app/src/renderer/app/services/deploy.service.ts
packages/app/src/renderer/app/services/dialogs.service.ts
packages/app/src/renderer/app/services/drag.service.ts
packages/app/src/renderer/app/services/environments.service.ts
packages/app/src/renderer/app/services/events.service.ts
packages/app/src/renderer/app/services/global-error-handler.ts
packages/app/src/renderer/app/services/logger-service.ts
packages/app/src/renderer/app/services/main-api-listener.service.ts
packages/app/src/renderer/app/services/main-api.service.ts
packages/app/src/renderer/app/services/migration.service.ts
packages/app/src/renderer/app/services/remote-config.service.ts
packages/app/src/renderer/app/services/server.service.ts
packages/app/src/renderer/app/services/settings.service.ts
packages/app/src/renderer/app/services/storage.service.ts
packages/app/src/renderer/app/services/sync-payloads.service.ts
packages/app/src/renderer/app/services/sync.service.ts
packages/app/src/renderer/app/services/templates.service.ts
packages/app/src/renderer/app/services/toasts.service.ts
packages/app/src/renderer/app/services/tour.service.ts
packages/app/src/renderer/app/services/ui.service.ts
packages/app/src/renderer/app/services/user.service.ts
packages/app/src/shared/shared-config.ts
packages/app/test/libs/bootstrap.ts
packages/app/test/libs/callbacks.ts
packages/app/test/libs/clipboard.ts
packages/app/test/libs/command-palette.ts
packages/app/test/libs/databuckets.ts
packages/app/test/libs/dialogs.ts
packages/app/test/libs/electron-mock.ts
packages/app/test/libs/environments-logs.ts
packages/app/test/libs/environments-proxy.ts
packages/app/test/libs/environments-settings.ts
packages/app/test/libs/environments.ts
packages/app/test/libs/file.ts
packages/app/test/libs/headers-utils.ts
packages/app/test/libs/http.ts
packages/app/test/libs/menu.ts
packages/app/test/libs/modals.ts
packages/app/test/libs/models.ts
packages/app/test/libs/navigation.ts
packages/app/test/libs/routes.ts
packages/app/test/libs/settings.ts
packages/app/test/libs/utils.ts
packages/app/test/libs/ws.ts
packages/app/test/specs/basic-calls.spec.ts
packages/app/test/specs/callbacks.spec.ts
packages/app/test/specs/changelog-modal.spec.ts
packages/app/test/specs/clipboard-copy.spec.ts
packages/app/test/specs/command-palette.spec.ts
packages/app/test/specs/compression.spec.ts
packages/app/test/specs/crud.spec.ts
packages/app/test/specs/data-storage.spec.ts
packages/app/test/specs/databuckets.spec.ts
packages/app/test/specs/enable-disable-routes.spec.ts
packages/app/test/specs/environment-hostname-restriction.spec.ts
packages/app/test/specs/environment-logs-recording.spec.ts
packages/app/test/specs/environment-logs.spec.ts
packages/app/test/specs/environments-duplicate.spec.ts
packages/app/test/specs/environments-incompatibility.spec.ts
packages/app/test/specs/export-openapi.spec.ts
packages/app/test/specs/external-changes-watcher.spec.ts
packages/app/test/specs/file.spec.ts
packages/app/test/specs/first-load.spec.ts
packages/app/test/specs/folders.spec.ts
packages/app/test/specs/global-route.spec.ts
packages/app/test/specs/headers.spec.ts
packages/app/test/specs/import-openapi.spec.ts
packages/app/test/specs/proxy.spec.ts
packages/app/test/specs/reimport-openapi.spec.ts
packages/app/test/specs/responses-rules.spec.ts
packages/app/test/specs/route-response-default.spec.ts
packages/app/test/specs/route-response-duplicate.spec.ts
packages/app/test/specs/routes-create-delete.spec.ts
packages/app/test/specs/routes-duplicate-to-env.spec.ts
packages/app/test/specs/routes-duplicate.spec.ts
packages/app/test/specs/routes-filter.spec.ts
packages/app/test/specs/schema-validation.spec.ts
packages/app/test/specs/settings.spec.ts
packages/app/test/specs/templating.spec.ts
packages/app/test/specs/tls.spec.ts
packages/app/test/specs/ui-interactions.spec.ts
packages/app/test/specs/ws.spec.ts
packages/cli/eslint.config.mjs
packages/cli/src/commands/dockerize.ts
packages/cli/src/commands/export.ts
packages/cli/src/commands/import.ts
packages/cli/src/commands/start.ts
packages/cli/src/commands/validate.ts
packages/cli/test/specs/cloud-data-loading.test.ts
packages/cli/test/specs/data-loading.test.ts
packages/cli/test/specs/data-validation.test.ts
packages/cli/test/specs/dockerize-command.test.ts
packages/cli/test/specs/env-vars-prefix.test.ts
packages/cli/test/specs/export-command.test.ts
packages/cli/test/specs/file-serving.test.ts
packages/cli/test/specs/file-watch.test.ts
packages/cli/test/specs/import-command.test.ts
packages/cli/test/specs/logging.test.ts
packages/cli/test/specs/run-from-openapi.test.ts
packages/cli/test/specs/run-multiple-mocks.test.ts
packages/cli/test/specs/run-single-mock.test.ts
packages/cli/test/specs/validate-command.test.ts
packages/commons-server/src/constants/server-messages.constants.ts
packages/commons-server/src/constants/ssl.constants.ts
packages/commons-server/src/libs/faker.ts
packages/commons-server/src/libs/filters.ts
packages/commons-server/src/libs/logger.ts
packages/commons-server/src/libs/requests.ts
packages/commons-server/src/libs/response-rules-interpreter.ts
packages/commons-server/src/libs/server/admin-api.ts
packages/commons-server/src/libs/server/crud.ts
packages/commons-server/src/libs/server/data-buckets.ts
packages/commons-server/src/libs/server/events-listeners.ts
packages/commons-server/src/libs/server/server.ts
packages/commons-server/src/libs/server/sse.ts
packages/commons-server/src/libs/server/ws.ts
packages/commons-server/src/libs/template-parser.ts
packages/commons-server/src/libs/utils.ts
packages/commons-server/test/libs/environment.ts
packages/commons-server/test/specs/server/admin-api/data-buckets.test.ts
packages/commons-server/test/specs/server/admin-api/disable-api.test.ts
packages/commons-server/test/specs/server/admin-api/env-vars.test.ts
packages/commons-server/test/specs/server/admin-api/global-state.test.ts
packages/commons-server/test/specs/server/admin-api/global-vars.test.ts
packages/commons-server/test/specs/server/admin-api/logs.test.ts
packages/commons/src/models/environment.model.ts
packages/commons/src/models/events.model.ts
packages/commons/src/models/faker.model.ts
packages/commons/src/models/folder.model.ts
packages/commons/src/models/migrations.model.ts
packages/commons/src/models/reorder.model.ts
packages/commons/src/models/route.model.ts
packages/commons/src/models/server.model.ts
packages/commons/src/utils/mutator-utils.ts
packages/commons/src/utils/utils.ts
packages/commons/test/specs/migrations.test.ts
packages/commons/test/specs/openapi-converter.test.ts
packages/commons/test/specs/utils.test.ts
packages/serverless/eslint.config.mjs
packages/serverless/src/libs/serverless.ts
packages/serverless/test/specs/serverless.test.ts
packages/app/  (114 files)
packages/cli/  (11 files)
packages/cloud/  (13 files)
packages/commons/  (12 files)
packages/commons-server/  (122 files)
packages/serverless/  (1 files)
scripts/  (1 files)
shared/  (1 files)
... (450 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "@mockoon/mockoon",
  "private": true,
  "version": "1.0.0",
  "author": {
    "name": "Mockoon (1kB SARL-S)",
    "email": "team@mockoon.com",
    "url": "https://mockoon.com/"
  },
  "description": "Mockoon is the easiest and quickest way to run mock APIs locally. No remote deployment, no account required, open source.",
  "license": "MIT",
  "repository": "https://github.com/mockoon/mockoon",
  "homepage": "https://mockoon.com",
  "bugs": {
    "url": "https://github.com/mockoon/mockoon/issues"
  },
  "funding": "https://mockoon.com/sponsor-us/",
  "prettier": {
    "singleQuote": true,
    "tabWidth": 2,
    "printWidth": 80,
    "trailingComma": "none",
    "endOfLine": "auto"
  },
  "scripts": {
    "lint": "npm run lint --workspaces",
    "format": "prettier . --check",
    "format:write": "prettier . --write",
    "set-versions": "node ./scripts/set-versions.mjs && npm install",
    "oldset-versions": "npm version --git-tag-version=false --workspaces $1 && npm install --workspace=@mockoon/app --workspace=@mockoon/cli --workspace=@mockoon/cloud --workspace=@mockoon/commons-server --workspace=@mockoon/serverless @mockoon/commons@$0 && npm install --workspace=@mockoon/app --workspace=@mockoon/cli --workspace=@mockoon/serverless @mockoon/commons-server@$0 && npm install --workspace=@mockoon/app @mockoon/cloud@$0",
    "publish": "npm publish --workspace=@mockoon/commons --workspace=@mockoon/commons-server --workspace=@mockoon/cloud --workspace=@mockoon/cli --workspace=@mockoon/serverless",
    "build:commons": "npm run build --workspace=@mockoon/commons",
    "build:commons:watch": "npm run build:watch --workspace=@mockoon/commons",
    "build:commons-server": "npm run build --workspace=@mockoon/commons-server",
    "build:commons-server:watch": "npm run build:watch --workspace=@mockoon/commons-server",
    "build:cloud": "npm run build --workspace=@mockoon/cloud",
    "build:cloud:watch": "npm run build:watch --workspace=@mockoon/cloud",
    "build:libs": "npm run build --workspace=@mockoon/commons --workspace=@mockoon/commons-server --workspace=@mockoon/cloud",
    "build:libs:watch": "concurrently \"npm run build:watch --workspace=@mockoon/commons\" \"npm run build:watch --workspace=@mockoon/commons-server\" \"npm run build:watch --workspace=@mockoon/cloud\"",
    "build:serverless": "npm run build --workspace=@mockoon/serverless",
    "build:cli": "npm run build --workspace=@mockoon/cli",
    "build:web:dev:watch": "npm run build:watch:web --workspace=@mockoon/app",
    "build:desktop:dev:watch": "npm run build:watch:all --workspace=@mockoon/app",
    "build:desktop:dev": "npm run build:dev:all --workspace=@mockoon/app",
    "build:desktop:ci": "npm run build:ci:all --workspace=@mockoon/app",
    "build:desktop:prod": "npm run build:prod:all --workspace=@mockoon/app",
    "build:web:prod": "npm run build:prod:web --workspace=@mockoon/app",
    "start:web:dev": "npm run start:web --workspace=@mockoon/app",
    "start:desktop:dev": "npm run start --workspace=@mockoon/app",
    "start:desktop:dev:2": "npm run start:2 --workspace=@mockoon/app",
    "start:desktop:dev:3": "npm run start:3 --workspace=@mockoon/app",
    "test:commons": "npm run test --workspace=@mockoon/commons",
    "test:commons-server": "npm run test --workspace=@mockoon/commons-server",
    "test:libs": "npm run test --workspace=@mockoon/commons --workspace=@mockoon/commons-server",
    "test:serverless": "npm run test --workspace=@mockoon/serverless",
    "test:cli": "npm run test --workspace=@mockoon/cli",
    "test:desktop:win": "npm run test:win --workspace=@mockoon/app",
    "test:desktop:mac": "npm run test:mac --workspace=@mockoon/app",
    "test:desktop:linux": "npm run test:linux --workspace=@mockoon/app",
    "package:desktop:win": "npm run package:win --workspace=@mockoon/app",
    "package:desktop:win:appx": "npm run package:win:appx --workspace=@mockoon/app",
    "package:desktop:mac": "npm run package:mac --workspace=@mockoon/app",
    "package:desktop:mac:unsigned": "npm run package:mac:unsigned --workspace=@mockoon/app",
    "package:desktop:linux": "npm run package:linux --workspace=@mockoon/app",
    "package:desktop:test:win": "npm run package:test:win --workspace=@mockoon/app",
    "package:desktop:test:mac": "npm run package:test:mac --workspace=@mockoon/app",
    "package:desktop:test:linux": "npm run package:test:linux --workspace=@mockoon/app",
    "deploy:web": "npm run deploy:web --workspace=@mockoon/app",
    "documentation:desktop": "npm run documentation --workspace=@mockoon/app"
  },
  "workspaces": [
    "packages/app",
    "packages/cli",
    "packages/cloud",
    "packages/commons",
    "packages/commons-server",
    "packages/serverless"
  ],
  "devDependencies": {
    "@eslint/js": "10.0.1",
    "@stylistic/eslint-plugin": "5.10.0",
    "@types/node": "24.13.2",
    "concurrently": "10.0.3",
    "eslint": "10.5.0",
    "eslint-config-prettier": "10.1.8",
    "eslint-plugin-prettier": "5.5.6",
    "glob": "13.0.6",
    "glob-bin": "1.1.0",
    "prettier": "3.8.4",
    "prettier-plugin-organize-imports": "4.3.0",
    "tsx": "4.22.4",
    "typescript": "5.9.3",
    "typescript-eslint": "8.61.1"
  },
  "allowScripts": {
    "esbuild@0.27.3": true,
    "esbuild@0.25.12": true,
    "esbuild@0.28.1": true,
    "esbuild@0.27.7": true,
    "@firebase/util@1.15.1": true,
    "@parcel/watcher@2.5.6": true,
    "edgedriver@6.3.0": true,
    "electron@41.2.1": true,
    "electron-winstaller@5.4.0": true,
    "geckodriver@6.1.0": true,
    "lmdb@3.5.1": true,
    "msgpackr-extract@3.0.4": true,
    "protobufjs@7.6.4": true,
    "unrs-resolver@1.12.2": true
  }
}

```
Context & Existing Test Patterns
Existing test files touched by the patch: packages/app/test/libs/environments.ts, packages/app/test/specs/databuckets.spec.ts, packages/app/test/specs/responses-rules.spec.ts, packages/cli/test/specs/auth-flags.test.ts, packages/cli/test/specs/logging.test.ts, packages/commons-server/test/libs/utils.ts, packages/commons-server/test/specs/server/admin-api/cors.test.ts, packages/commons-server/test/specs/server/admin-api/data-buckets.test.ts, packages/commons-server/test/specs/server/admin-api/env-vars.test.ts, packages/commons-server/test/specs/server/admin-api/global-state.test.ts, packages/commons-server/test/specs/server/admin-api/global-vars.test.ts, packages/commons-server/test/specs/server/admin-api/logs.test.ts, packages/commons/test/specs/utils.test.ts, packages/serverless/test/specs/serverless.test.ts
Repository top-level entries: .editorconfig, .github, .gitignore, .npmrc, .prettierignore, .vscode, CONTRIBUTING.md, LICENSE.md, README.md, backers.md, package-lock.json, package.json, packages, scripts, shared, tsconfig.json
Project's own test patterns and conventions:
### packages/app/test/specs/compression.spec.ts
```
import { createServer, Server } from 'http';
import { brotliCompress, deflate, gzip, zstdCompress } from 'zlib';
import environments from '../libs/environments';
import environmentsLogs from '../libs/environments-logs';
import headersUtils from '../libs/headers-utils';
import http from '../libs/http';
import { HttpCall } from '../libs/models';
import navigation from '../libs/navigation';
import routes from '../libs/routes';

const compressionLibs = {
  gzip,
  deflate,
  br: brotliCompress,
  zstd: zstdCompress
};

const fakeServer = () =>
  new Promise<Server>((resolve) => {
    const server = createServer((req, res) => {
      const encoding = req.headers['accept-encoding'] as string;

      res.statusCode = 200;

      if (encoding && encoding !== 'identity') {
        compressionLibs[encoding](`${encoding}test`, (error, result) => {
          if (error) {
            throw error;
          }
          res.setHeader('Content-Encoding', encoding);
          res.write(result);
          res.end();
        });
      } else {
        res.write('test');
        res.end();
      }
    }).listen(3999, () => {
      resolve(server);
    });
  });

const testCases: { assertTitle: string; assertBody: string; call: HttpCall }[] =
  [
    {
      assertTitle: 'Body',
      assertBody: 'test',
      call: {
        description:
          'should call GET /test and verify logs body is not encoded',
        protocol: 'http',
        path: '/test',
        headers: { 'Accept-Encoding': 'identity' },
        method: 'GET',
        testedResponse: {
          status: 200,
          body: 'test'
        }
      }
    },
    {
      assertTitle: 'Body (decompressed)',
      assertBody: 'gziptest',
      call: {
        description:
          'should call GET /test and verify logs body is decoded (gzip)',
        protocol: 'http',
        headers: { 'Accept-Encoding': 'gzip' },
        path: '/test',
        method: 'GET',
        testedResponse: {
          status: 200
        }
      }
    },
    {
      assertTitle: 'Body (decompressed)',
      assertBody: 'deflatetest',
      call: {
        description:
          'should call GET /test and verify logs body is decoded (deflate)',
        protocol: 'http',
        headers: { 'Accept-Encoding': 'deflate' },
        path: '/test',
        method: 'GET',
        testedResponse: {
          status: 200
        }
      }
    },
    {
      assertTitle: 'Body (decompressed)',
      assertBody: 'brtest',
      call: {
        description:
          'should call GET /test and verify logs body is decoded (br)',
        protocol: 'http',
        headers: { 'Accept-Encoding': 'br' },
        path: '/test',
        method: 'GET',
        testedResponse: {
          status: 200
        }
      }
    },
    {
      assertTitle: 'Body (decompressed)',
      assertBody: 'zstdtest',
      call: {
        description:
          'should call GET /test and verify logs body is decoded (zstd)',
        protocol: 'http',
        headers: { 'Accept-Encoding': 'zstd' },
        path: '/test',
        method: 'GET',
        testedResponse: {
          status: 200
        }
      }
    }
  ];

describe('Proxy to server with zipped content', () => {
  let server: Server;

  before(async () => {
    server = await fakeServer();
  });

  it('should open and start the environment', async () => {
    await environments.open('compression');
    await environments.start();
    await navigation.switchView('ENV_LOGS');
  });

  testCases.forEach((testCase) => {
    it(testCase.call.description, async () => {
      await http.assertCallWithPort(testCase.call, 3004);
      await environmentsLogs.select(1);
      await environmentsLogs.switchTab('RESPONSE');
      await environmentsLogs.assertLogBody(testCase.assertBody, 'response');
      await environmentsLogs.assertLogItemTitle(
        testCase.assertTitle,
        'response',
        5
      );
    });
  });

  it('should auto mock one call and verify the body and headers', async () => {
    await environmentsLogs.clickMockButton(1);
    await routes.assertBody('zstdtest');
    await routes.switchTab('HEADERS');
    await headersUtils.assertHeadersValues('route-response-headers', {
      'content-encoding': undefined,
      'transfer-encoding': undefined
    });
  });

  after(() => {
    server.close();
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

