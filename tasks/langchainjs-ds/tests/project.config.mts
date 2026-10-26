import { defineConfig } from "vitest/config";

// Runner for the project's own unit tests for the affected area. It mirrors the
// package's vitest defaults but pins a writable cache directory and runs the
// project's test files unchanged, from the package root.
export default defineConfig({
  cacheDir: "/tmp/langchainjs-project-vite",
  test: {
    globals: true,
    environment: "node",
    include: ["src/tests/filters.test.ts", "src/tests/vectorstores.test.ts"],
    setupFiles: ["dotenv/config"],
    testTimeout: 30000,
    hookTimeout: 30000,
    pool: "forks",
    fileParallelism: false,
    reporters: ["default"],
  },
});
