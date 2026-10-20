<instruction_md>
# An outside call changed the mock and the call log showed a cookie

## What we observed

We were running a mock for a service under test. From another machine, and without any credential, we sent a POST to the admin API at `/mockoon-admin` that sets a global variable. That call was accepted. The mock's later response included the value we had written.

We sent a second POST, again with no credential, that set a process environment variable the mock is not supposed to expose. That call was accepted too, and the process was then running with the value.

Those admin responses told a browser that a different website was allowed to read them. A page we loaded from another origin repeated the call and could see the result.

Earlier we had made an ordinary mock call that carried a cookie. We then requested the admin API's call log. The cookie from that mock call was in the log in full.

## Impact

A caller who was never given access to operate the mock can change what the mock serves, can change a process environment variable, and can read credentials that a client attached to an ordinary mock call. Because another website can read the admin response, a page the operator has open can do this to a mock on the same machine.

## What must keep working

Ordinary mock endpoints must still answer. A normal mock call that carries a cookie, or an API key, must still receive the mocked response.

The record of a mock call must still include the path and the values of ordinary headers that are not credentials.

When a caller sends a bearer credential, the record must still show that a bearer credential was used, and it must still leave out the secret itself.

Starting the mock with the admin API turned off must still serve the mocked endpoints.
</instruction_md>
<task_metadata_json>
{
  "entry_point": "Unauthenticated HTTP requests to the running mock's admin API, and the transaction record written when a mock call is logged.",
  "techniques": [
    1,
    2,
    4,
    5,
    7,
    9,
    12
  ],
  "trap": {
    "paths": [
      "packages/commons-server/src/libs/server/events-listeners.ts",
      "packages/commons-server/src/libs/utils.ts"
    ],
    "contract": "A mock call that carries a cookie or an API key still receives the mocked response, and the call record still includes the path, the values of ordinary non-credential headers, and the fact that a bearer credential was used, without the secret."
  },
  "fix_places": [
    "packages/commons-server/src/libs/server/admin-api.ts",
    "packages/commons-server/src/libs/server/events-listeners.ts",
    "packages/commons-server/src/libs/utils.ts",
    "packages/commons/src/utils/utils.ts"
  ],
  "unrelated_files": [
    "packages/app/src/main/libs/server-management.ts",
    "packages/app/src/renderer/app/components/environment-settings/environment-settings.component.ts",
    "packages/app/src/renderer/app/models/main-api.model.ts",
    "packages/app/src/renderer/app/models/store.model.ts",
    "packages/app/src/renderer/app/services/server.service.ts",
    "packages/app/src/shared/shared-config.ts",
    "packages/cli/src/commands/start.ts",
    "packages/commons-server/src/constants/server-messages.constants.ts",
    "packages/commons-server/src/libs/logger.ts",
    "packages/commons-server/src/libs/server/server.ts",
    "packages/commons/src/models/server.model.ts",
    "packages/serverless/src/libs/serverless.ts"
  ],
  "test_justifications": {
    "test_security_unauthenticated_global_variable": "From another machine, and without any credential, we sent a POST to the admin API at `/mockoon-admin` that sets a global variable. That call was accepted. The mock's later response included the value we had written.",
    "test_security_unauthenticated_env_write": "We sent a second POST, again with no credential, that set a process environment variable the mock is not supposed to expose. That call was accepted too, and the process was then running with the value.",
    "test_security_cross_origin_admin": "A page we loaded from another origin repeated the call and could see the result.",
    "test_security_admin_log_cookie": "We then requested the admin API's call log. The cookie from that mock call was in the log in full.",
    "test_security_recorded_call_cookie": "can read credentials that a client attached to an ordinary mock call.",
    "test_security_recorded_call_api_key": "can read credentials that a client attached to an ordinary mock call.",
    "test_functional_mock_route_answers": "Ordinary mock endpoints must still answer.",
    "test_functional_mock_call_with_cookie": "A normal mock call that carries a cookie, or an API key, must still receive the mocked response.",
    "test_functional_mock_call_with_api_key": "A normal mock call that carries a cookie, or an API key, must still receive the mocked response.",
    "test_functional_record_keeps_ordinary_header": "The record of a mock call must still include the path and the values of ordinary headers that are not credentials.",
    "test_functional_record_shows_bearer_scheme": "When a caller sends a bearer credential, the record must still show that a bearer credential was used, and it must still leave out the secret itself.",
    "test_functional_admin_disabled_mock_answers": "Starting the mock with the admin API turned off must still serve the mocked endpoints."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "packages/commons-server/src/libs/server/admin-api.ts",
      "search": "  app.post(`${adminApiPrefix}/global-vars`, setGlobalVarHandler);",
      "replace": "  app.post(`${adminApiPrefix}/global-vars`, (_req, res) => {\n    res.status(401).send({ message: 'Unauthorized' });\n  });"
    }
  ],
  "removal": [
    {
      "file": "packages/commons-server/src/libs/server/admin-api.ts",
      "search": "  app.use(`${adminApiPrefix}*`, (req, res, next) => {\n    res.setHeaders(\n      new Headers({\n        'Access-Control-Allow-Origin': '*',\n        'Access-Control-Allow-Methods':\n          'GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS',\n        'Access-Control-Allow-Headers':\n          'Content-Type, Origin, Accept, Authorization, Content-Length, X-Requested-With'\n      })\n    );\n    next();\n  });\n",
      "replace": "  app.use(`${adminApiPrefix}*`, (req, res, _next) => {\n    res.status(403).end();\n  });\n"
    },
    {
      "file": "packages/commons-server/src/libs/server/events-listeners.ts",
      "search": "const authorizationHeaders = ['authorization', 'proxy-authorization'];\nconst filterAuthorizationHeaders = (header: Header) => {\n  if (authorizationHeaders.includes(header.key.toLowerCase())) {\n    const headerSplit = header.value.split(' ');\n\n    header.value = headerSplit.length === 1 ? '***' : `${headerSplit[0]} ***`;\n  }\n\n  return header;\n};\n",
      "replace": "const authorizationHeaders = ['authorization', 'proxy-authorization'];\nconst filterAuthorizationHeaders = (header: Header) => {\n  if (authorizationHeaders.includes(header.key.toLowerCase()) || header.key) {\n    header.value = '***';\n  }\n\n  return header;\n};\n"
    }
  ],
  "alternative": [
    {
      "file": "packages/commons-server/src/libs/server/admin-api.ts",
      "search": "import { Environment, EnvironmentSchema, Transaction } from '@mockoon/commons';\nimport { Express, Request, Response } from 'express';\nimport { MockoonServer } from './server';\nimport { Sse } from './sse';\n",
      "replace": "import { Environment, EnvironmentSchema, Transaction } from '@mockoon/commons';\nimport { Express, Request, Response } from 'express';\nimport { randomBytes } from 'node:crypto';\nimport { MockoonServer } from './server';\nimport { Sse } from './sse';\n"
    },
    {
      "file": "packages/commons-server/src/libs/server/admin-api.ts",
      "search": "  app.use(`${adminApiPrefix}*`, (req, res, next) => {\n    res.setHeaders(\n      new Headers({\n        'Access-Control-Allow-Origin': '*',\n        'Access-Control-Allow-Methods':\n          'GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS',\n        'Access-Control-Allow-Headers':\n          'Content-Type, Origin, Accept, Authorization, Content-Length, X-Requested-With'\n      })\n    );\n    next();\n  });\n",
      "replace": "  const adminCredential = randomBytes(32).toString('hex');\n\n  app.use(`${adminApiPrefix}*`, (req, res, next) => {\n    if (req.method === 'OPTIONS') {\n      res.status(403).end();\n\n      return;\n    }\n\n    const authorization = req.get('authorization') ?? '';\n    const bearer = /^bearer\\s+(\\S+)/i.exec(authorization);\n    const provided = bearer ? bearer[1] : '';\n\n    if (!provided || provided !== adminCredential) {\n      res.status(401).send({ message: 'Unauthorized' });\n\n      return;\n    }\n\n    next();\n  });\n"
    },
    {
      "file": "packages/commons-server/src/libs/server/events-listeners.ts",
      "search": "const authorizationHeaders = ['authorization', 'proxy-authorization'];\nconst filterAuthorizationHeaders = (header: Header) => {\n  if (authorizationHeaders.includes(header.key.toLowerCase())) {\n    const headerSplit = header.value.split(' ');\n\n    header.value = headerSplit.length === 1 ? '***' : `${headerSplit[0]} ***`;\n  }\n\n  return header;\n};\n",
      "replace": "const authorizationHeaders = ['authorization', 'proxy-authorization'];\nconst credentialHeaders = [\n  'cookie',\n  'set-cookie',\n  'x-api-key',\n  'api-key',\n  'x-auth-token'\n];\nconst filterAuthorizationHeaders = (header: Header) => {\n  const key = header.key.toLowerCase();\n\n  if (authorizationHeaders.includes(key)) {\n    const headerSplit = header.value.split(' ');\n\n    header.value = headerSplit.length === 1 ? '***' : `${headerSplit[0]} ***`;\n  } else if (credentialHeaders.includes(key)) {\n    header.value = '***';\n  }\n\n  return header;\n};\n"
    }
  ]
}
</check_patches_json>
