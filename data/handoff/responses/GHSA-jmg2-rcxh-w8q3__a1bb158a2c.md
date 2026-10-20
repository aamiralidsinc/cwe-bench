<instruction_md>
# Compiled module source was readable from another website

While an rspack build was running with the analysis plugin, the report server started on this machine. From our internal docs site, open in another browser tab, I issued the same request the report page uses to load compiled module source. The response body included a string that exists only in our application source, plus build metadata. The server did not ask for a credential, and it allowed the docs site to read that body.

I repeated the request so that it presented the docs site's name rather than this machine. The server still returned the source.

I also opened a separate session against that same report server, not the one the report page on this machine was already using, and that session received the compiled module source as well.

## Impact

Compiled module source and the build metadata shown in the report left the machine. A page that is not the local report could read them, and so could a request that named a site other than this machine. Secrets and proprietary logic compiled into the build were included.

## What must keep working

- The report page on this machine must still be able to load compiled module source and build metadata. That includes a request that uses the localhost name, a request that uses a loopback address, and a request that is not cross-site.
- The live updates the report page receives while the build is running must keep working for that local page.
- Choosing the port the report server listens on must still be honored.
- A second report server started for another profile in the same session must still let this machine read that profile's module source.
</instruction_md>
<task_metadata_json>
{
  "entry_point": "RsdoctorSDK report server, including POST /api/data/key and server.socketUrl",
  "techniques": [
    1,
    5,
    7,
    9,
    12
  ],
  "trap": {
    "paths": [
      "packages/sdk/src/sdk/server/socket/index.ts"
    ],
    "contract": "A non-cross-site request from this machine, including the localhost name and a loopback address, still receives compiled module source; the live connection string already published to that local report page still connects; the listen port the caller chose is kept; a second profile server still serves that profile's source to this machine."
  },
  "fix_places": [
    "packages/sdk/src/sdk/server/index.ts",
    "packages/sdk/src/sdk/server/security.ts",
    "packages/sdk/src/sdk/server/socket/index.ts"
  ],
  "unrelated_files": [
    "packages/cli/src/commands/analyze.ts",
    "packages/cli/src/commands/stats-analyze.test.ts",
    "packages/cli/src/commands/stats-analyze.ts",
    "packages/components/src/utils/data/local.ts",
    "packages/components/src/utils/socket.ts",
    "packages/core/src/inner-plugins/utils/config.ts",
    "packages/rspack-plugin/src/multiple.ts",
    "packages/rspack-plugin/src/plugin.ts",
    "packages/rspack-plugin/tests/plugin.test.ts",
    "packages/sdk/src/sdk/multiple/primary.ts",
    "packages/sdk/src/sdk/multiple/server.ts",
    "packages/sdk/src/sdk/sdk/index.ts",
    "packages/sdk/src/sdk/server/fakeServer.ts",
    "packages/sdk/tests/sdk/core/atomic-write.test.ts",
    "packages/sdk/tests/server/apis/project.test.ts",
    "packages/sdk/tests/server/security.test.ts",
    "packages/sdk/tests/server/socket.test.ts",
    "packages/sdk/tests/utils.ts",
    "packages/types/src/plugin/plugin.ts",
    "packages/types/src/sdk/instance.ts",
    "packages/types/src/sdk/server/index.ts",
    "packages/utils/src/common/global-config.ts",
    "packages/utils/tests/server.test.ts"
  ],
  "test_justifications": {
    "test_security_foreign_page_cannot_read_module_source": "The response body included a string that exists only in our application source, plus build metadata. The server did not ask for a credential, and it allowed the docs site to read that body.",
    "test_security_foreign_site_name_cannot_read_module_source": "I repeated the request so that it presented the docs site's name rather than this machine. The server still returned the source.",
    "test_security_separate_session_cannot_receive_module_source": "I also opened a separate session against that same report server, not the one the report page on this machine was already using, and that session received the compiled module source as well.",
    "test_security_forged_session_cannot_receive_module_source": "I also opened a separate session against that same report server, not the one the report page on this machine was already using, and that session received the compiled module source as well.",
    "test_functional_local_page_still_loads_module_source": "The report page on this machine must still be able to load compiled module source and build metadata. That includes a request that uses the localhost name, a request that uses a loopback address, and a request that is not cross-site.",
    "test_functional_localhost_name_still_loads_module_source": "That includes a request that uses the localhost name, a request that uses a loopback address, and a request that is not cross-site.",
    "test_functional_loopback_address_still_loads_module_source": "That includes a request that uses the localhost name, a request that uses a loopback address, and a request that is not cross-site.",
    "test_functional_live_updates_still_connect_for_local_page": "The live updates the report page receives while the build is running must keep working for that local page.",
    "test_functional_chosen_port_is_honored": "Choosing the port the report server listens on must still be honored.",
    "test_functional_second_profile_server_still_loads_module_source": "A second report server started for another profile in the same session must still let this machine read that profile's module source."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "    this.app.use(cors());",
      "replace": "    this.app.use((req, res, next) => {\n      const origin = req.headers.origin;\n      const localOrigin =\n        /^https?:\\/\\/(?:(?:[^:]+\\.)?localhost|127\\.0\\.0\\.1|\\[::1\\])(?::\\d+)?$/;\n      if (typeof origin === 'string' && !localOrigin.test(origin)) {\n        res.statusCode = 403;\n        res.end();\n        return;\n      }\n      next();\n    });\n    this.app.use(cors());"
    }
  ],
  "removal": [
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "    this.app.use(cors());",
      "replace": "    this.app.use((_req, res) => {\n      res.statusCode = 403;\n      res.end();\n    });"
    }
  ],
  "alternative": [
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "import { ServerResponse } from 'http';",
      "replace": "import { ServerResponse } from 'http';\nimport { randomBytes } from 'node:crypto';\nimport { isIP } from 'node:net';"
    },
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "export class RsdoctorServer implements SDK.RsdoctorServerInstance {",
      "replace": "const LOCAL_PAGE_ORIGIN =\n  /^https?:\\/\\/(?:(?:[^:]+\\.)?localhost|127\\.0\\.0\\.1|\\[::1\\])(?::\\d+)?$/;\n\nfunction hostnameFromHostHeader(host: string) {\n  if (host.startsWith('[')) {\n    const end = host.indexOf(']');\n    return end === -1 ? '' : host.slice(1, end).toLowerCase();\n  }\n  return host.split(':')[0].toLowerCase();\n}\n\nfunction hostHeaderAllowed(host: string | string[] | undefined) {\n  if (typeof host !== 'string' || host.length === 0) {\n    return false;\n  }\n  const hostname = hostnameFromHostHeader(host);\n  return (\n    hostname === 'localhost' ||\n    hostname.endsWith('.localhost') ||\n    isIP(hostname) !== 0\n  );\n}\n\nfunction pageOriginAllowed(origin: string | string[] | undefined) {\n  if (typeof origin === 'undefined') {\n    return true;\n  }\n  return typeof origin === 'string' && LOCAL_PAGE_ORIGIN.test(origin);\n}\n\nexport class RsdoctorServer implements SDK.RsdoctorServerInstance {"
    },
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "  private _printServerUrl: boolean;\n\n  constructor(",
      "replace": "  private _printServerUrl: boolean;\n\n  private _sessionKey = randomBytes(16).toString('hex');\n\n  constructor("
    },
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "  public get socketUrl(): ISocketType {\n    return {\n      port: this.port,\n      socketUrl: `ws://localhost:${this.port}`,\n    };\n  }",
      "replace": "  public get socketUrl(): ISocketType {\n    return {\n      port: this.port,\n      socketUrl: `ws://127.0.0.1:${this.port}?token=${this._sessionKey}`,\n    };\n  }"
    },
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "    this._socket = new Socket({\n      sdk: this.sdk,\n      server: this._server.server,\n      port: this.port,\n    });",
      "replace": "    this._socket = new Socket({\n      sdk: this.sdk,\n      server: this._server.server,\n      port: this.port,\n      token: this._sessionKey,\n    });"
    },
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "    this.app.use(cors());",
      "replace": "    this.app.use((req, res, next) => {\n      const host = req.headers.host || req.headers[':authority'];\n      if (!hostHeaderAllowed(host) || !pageOriginAllowed(req.headers.origin)) {\n        res.statusCode = 403;\n        res.end();\n        return;\n      }\n      next();\n    });\n    this.app.use(\n      cors({\n        origin: LOCAL_PAGE_ORIGIN,\n      }),\n    );"
    },
    {
      "file": "packages/sdk/src/sdk/server/index.ts",
      "search": "          res.setHeader('Access-Control-Allow-Origin', '*');\n          res.setHeader('Access-Control-Allow-Credentials', 'true');\n          res.statusCode = 200;",
      "replace": "          res.statusCode = 200;"
    },
    {
      "file": "packages/sdk/src/sdk/server/socket/index.ts",
      "search": "interface SocketOptions {\n  sdk: SDK.RsdoctorBuilderSDKInstance;\n  server: Server;\n  port: number;\n}",
      "replace": "interface SocketOptions {\n  sdk: SDK.RsdoctorBuilderSDKInstance;\n  server: Server;\n  port: number;\n  token?: string;\n}"
    },
    {
      "file": "packages/sdk/src/sdk/server/socket/index.ts",
      "search": "  public bootstrap() {\n    this.server = new WebSocketServer({ server: this.options.server });",
      "replace": "  public bootstrap() {\n    this.server = new WebSocketServer({\n      server: this.options.server,\n      verifyClient: ({ req }) => {\n        const expected = this.options.token;\n        if (!expected || !req.url) {\n          return false;\n        }\n        const presented = new URL(req.url, 'http://127.0.0.1').searchParams.get(\n          'token',\n        );\n        return presented === expected;\n      },\n    });"
    }
  ]
}
</check_patches_json>
