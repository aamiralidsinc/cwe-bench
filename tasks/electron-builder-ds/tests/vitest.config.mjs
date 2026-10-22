// Pristine verifier config. test.sh compiles the workspace packages from their TypeScript source in
// /app (as the repo's own `tsc --build` does) and the tests load that compiled output natively,
// through the same package names the repo's own tests use.
import path from "node:path"

import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    environment: "node",
    // The product logger snapshots the debug flag when it loads; set it before any module does.
    env: { DEBUG: "electron-builder" },
    globals: true,
    include: ["**/*.test.ts", "**/*Test.ts"],
    setupFiles: [path.join(import.meta.dirname, "support/setup.ts")],
    server: { deps: { external: [/\/packages\/[^/]+\/out\//] } },
    testTimeout: 30_000,
    hookTimeout: 30_000,
    pool: "forks",
    fileParallelism: false,
    cache: false,
  },
})
