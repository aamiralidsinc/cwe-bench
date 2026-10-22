import { defineConfig } from "vitest/config";

// Fixed runner settings for the project's own tests for the affected area. The
// test files are restored from pristine copies at grade time; this config only
// supplies the Node environment and a writable cache dir, so the run does not
// depend on (or trust) a config file inside the submitted tree.
export default defineConfig({
  cacheDir: "/tmp/ckan-vite-project",
  test: {
    globals: true,
    environment: "node",
    include: ["tests/**/*.test.ts"]
  }
});
