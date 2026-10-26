// Hidden verifier jest config for the backend-core package (shared outbound
// fetch helper). No Docker testcontainers setup.
const path = require("path")

const coreRoot = "/workspace/packages/backend-core"
const at = (rel) => path.join(coreRoot, rel)

module.exports = {
  rootDir: coreRoot,
  testEnvironment: "node",
  testTimeout: 60000,
  setupFiles: [at("tests/jestEnv.ts")],
  transform: {
    "^.+\\.(ts|tsx)$": ["@swc/jest"],
  },
  moduleFileExtensions: ["js", "mjs", "cjs", "jsx", "ts", "tsx", "json", "node"],
  moduleNameMapper: {
    "@budibase/types": at("../types/src"),
    "@budibase/shared-core": [at("../shared-core/src")],
  },
}
