import { defineConfig } from "vitest/config";

// The product lives in /workspace (the solver's tree, built by the verifier).
// This hidden suite is copied to /workspace/.htests and run from there with
// the project's dependency tree, so nothing under /workspace/tests is run.
export default defineConfig({
  cacheDir: "/tmp/k8s-mcp-vite-hidden",
  server: {
    fs: { allow: ["/workspace"] },
  },
  test: {
    globals: true,
    environment: "node",
    include: ["security/**/*.test.ts", "functional/**/*.test.ts"],
    setupFiles: ["./setup.ts"],
    testTimeout: 60000,
    hookTimeout: 60000,
    pool: "forks",
    fileParallelism: false,
    reporters: ["default"],
  },
});
