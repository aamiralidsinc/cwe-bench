import { defineConfig } from "vitest/config";

// Hidden suites. They live in /workspace/.htests at grading time and import the
// product sources from the solver's tree, so any implementation of the rule is
// exercised. Kept offline and deterministic.
export default defineConfig({
  cacheDir: "/tmp/langchainjs-hidden-vite",
  server: {
    fs: { allow: ["/workspace"] },
  },
  test: {
    globals: true,
    environment: "node",
    include: ["security/**/*.test.ts", "functional/**/*.test.ts"],
    testTimeout: 30000,
    hookTimeout: 30000,
    pool: "forks",
    fileParallelism: false,
    reporters: ["default"],
  },
});
