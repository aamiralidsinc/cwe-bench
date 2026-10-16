// Pristine verifier config: runs the hidden tests against the @better-auth/sso *source* in
// /app (so the agent's changes under packages/sso/src are exercised), resolving the workspace
// the same way the repo's own tests do. Placed at /app by test.sh at grading time.
import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

const APP = path.dirname(fileURLToPath(import.meta.url));
const SSO = path.join(APP, "packages/sso/src");

export default defineConfig({
	resolve: {
		conditions: ["dev-source"],
		alias: [
			{ find: /^@better-auth\/sso\/client$/, replacement: path.join(SSO, "client.ts") },
			{ find: /^@better-auth\/sso$/, replacement: path.join(SSO, "index.ts") },
		],
	},
	test: {
		environment: "node",
		globals: false,
		testTimeout: 30_000,
		hookTimeout: 30_000,
		pool: "forks",
		fileParallelism: false,
		cache: false,
		include: ["packages/sso/__verifier__/**/*.test.ts"],
	},
});
