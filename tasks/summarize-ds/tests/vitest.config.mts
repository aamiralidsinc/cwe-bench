import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// The product source lives in /app (the solver's tree). The verifier runs from a
// pristine copy outside the repo with /app/node_modules linked in, so nothing under
// /app/tests is ever executed.
const here = dirname(fileURLToPath(import.meta.url));
const APP = resolve(process.env.APP_DIR ?? "/app");

export default defineConfig({
  resolve: {
    alias: [
      { find: "@app/core", replacement: resolve(APP, "packages/core/src/content/index.ts") },
      { find: "@app/daemon-server", replacement: resolve(APP, "src/daemon/server.ts") },
    ],
  },
  server: {
    fs: { allow: [APP, here] },
  },
  test: {
    globals: false,
    environment: "node",
    include: ["security/**/*.test.ts", "functional/**/*.test.ts"],
    setupFiles: ["./setup.ts"],
    testTimeout: 40000,
    hookTimeout: 40000,
    pool: "forks",
    fileParallelism: false,
    reporters: ["default"],
  },
});
