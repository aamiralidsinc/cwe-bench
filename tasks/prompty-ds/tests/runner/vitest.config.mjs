/**
 * vitest configuration for the hidden TypeScript suites.
 *
 * It is copied next to the core package at grade time; the test files are
 * copied into `_verifier/` below the package root. `@prompty/core` resolves
 * to the restored source rather than a built `dist/` (the artifact excludes
 * build outputs), matching how the packages are used in the workspace.
 */
import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

const coreSrc = fileURLToPath(new URL("./src/index.ts", import.meta.url));

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["_verifier/**/*.test.ts"],
  },
  resolve: {
    alias: { "@prompty/core": coreSrc },
  },
  cacheDir: "/tmp/prompty-vitest-cache",
});
