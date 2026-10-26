import path from "path";

const ROOT = process.env.ATLAS_ROOT || "/workspace";
const SRC = path.join(ROOT, "dashboard/src");
const HERE = path.join(ROOT, "dashboard/.htests");

const alias = {
  "@": SRC,
  "@components": path.join(SRC, "components"),
  "@utils": path.join(SRC, "utils"),
  "@api": path.join(SRC, "api"),
  "@views": path.join(SRC, "views"),
  "@redux": path.join(SRC, "redux"),
  "@contexts": path.join(SRC, "contexts"),
  "@models": path.join(SRC, "models"),
  "@hooks": path.join(SRC, "hooks"),
  "@services": path.join(SRC, "services"),
  "@styles": path.join(SRC, "styles")
};

export default {
  esbuild: { jsx: "automatic" },
  cacheDir: path.join(HERE, ".vite-cache"),
  resolve: { alias },
  test: {
    globals: true,
    environment: "jsdom",
    root: HERE,
    include: ["functional/**/*.test.ts", "functional/**/*.test.tsx"],
    testTimeout: 120000,
    hookTimeout: 120000,
    fileParallelism: false,
    pool: "forks",
    poolOptions: { forks: { singleFork: true } },
    reporters: ["default", ["junit", { outputFile: process.env.JUNIT_OUT || path.join(HERE, "functional-results.xml") }]]
  }
};
