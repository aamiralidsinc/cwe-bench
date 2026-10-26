// Hidden verifier jest config for the server package.
// Mirrors packages/server/jest.config.ts module resolution and the swc transform,
// without the repo's globalSetup/jestSetup (those start Docker testcontainers).
const path = require("path")

const serverRoot = "/workspace/packages/server"
const at = (rel) => path.join(serverRoot, rel)

module.exports = {
  rootDir: serverRoot,
  testEnvironment: "node",
  testTimeout: 60000,
  setupFiles: [at("src/tests/jestEnv.ts")],
  transform: {
    "^.+\\.(ts|tsx)$": ["@swc/jest"],
    "^.+\\.(js|jsx|mjs|cjs)$": ["@swc/jest"],
  },
  transformIgnorePatterns: [
    "/node_modules/(?!svelte/|esm-env/|devalue/|chokidar/|readdirp/).*",
  ],
  moduleFileExtensions: [
    "js",
    "mjs",
    "cjs",
    "jsx",
    "ts",
    "tsx",
    "json",
    "node",
    "svelte",
  ],
  moduleNameMapper: {
    "@budibase/backend-core/(.*)": at("../backend-core/$1"),
    "@budibase/shared-core/(.*)": at("../shared-core/$1"),
    "@budibase/backend-core": at("../backend-core/src"),
    "@budibase/shared-core": at("../shared-core/src"),
    "@budibase/types": at("../types/src"),
    "@budibase/string-templates/(.*)": at("../string-templates/$1"),
    "@budibase/string-templates": at("../string-templates/src"),
    "^chokidar$": at("__mocks__/chokidar.ts"),
    "^chat$": at("__mocks__/chat.ts"),
    "^@chat-adapter/discord$": at("__mocks__/chat-adapter-discord.ts"),
    "^@chat-adapter/slack$": at("__mocks__/chat-adapter-slack.ts"),
    "^@chat-adapter/teams$": at("__mocks__/chat-adapter-teams.ts"),
    "^@chat-adapter/telegram$": at("__mocks__/chat-adapter-telegram.ts"),
    "^@chat-adapter/state-memory$": at("__mocks__/chat-adapter-state-memory.ts"),
    "^@chat-adapter/state-ioredis$":
      at("__mocks__/chat-adapter-state-ioredis.ts"),
    "@budibase/pro": at("../pro/src"),
  },
}
