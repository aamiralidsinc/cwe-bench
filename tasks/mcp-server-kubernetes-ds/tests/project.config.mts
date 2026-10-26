import { defineConfig } from "vitest/config";

// The project's own unit tests for the affected tools, restored from pristine
// copies before the run so they exercise the solver's product source.
export default defineConfig({
  cacheDir: "/tmp/k8s-mcp-vite-project",
  test: {
    globals: true,
    environment: "node",
    include: [
      "tests/kubectl-context.unit.test.ts",
      "tests/kubectl-reconnect.unit.test.ts",
    ],
    testTimeout: 60000,
    hookTimeout: 60000,
    pool: "forks",
    fileParallelism: false,
    reporters: ["default"],
  },
});
