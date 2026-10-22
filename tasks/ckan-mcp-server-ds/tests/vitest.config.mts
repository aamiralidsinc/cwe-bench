import { defineConfig } from "vitest/config";

// The product source lives in /workspace (the solver's tree, built by the task
// image). The verifier copies this hidden suite to /workspace/.htests and runs
// it there with the project's dependency tree, so nothing under
// /workspace/tests is ever executed.
export default defineConfig({
  cacheDir: "/tmp/ckan-vite-hidden",
  server: {
    fs: { allow: ["/workspace"] }
  },
  test: {
    globals: true,
    environment: "node",
    include: ["security/**/*.test.ts", "functional/**/*.test.ts"],
    setupFiles: ["./setup.ts"],
    testTimeout: 40000,
    hookTimeout: 40000,
    pool: "forks",
    fileParallelism: false,
    reporters: ["default"]
  }
});
