/**
 * Hidden-suite vitest configuration.
 *
 * The verifier copies the agent's restored /workspace to /run/kiota, links the pristine
 * dependency tree from /opt/kiota, and drops the hidden suites under /run/kiota/.htests.
 * Workspace packages resolve to their TypeScript sources so the agent's source is what runs,
 * independent of any build output.
 */
import { defineConfig } from "vitest/config";

const ROOT = "/run/kiota";

function workspace(name: string, entry: string) {
	return {
		find: new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`),
		replacement: `${ROOT}/${entry}`,
	};
}

export default defineConfig({
	root: ROOT,
	cacheDir: `${ROOT}/.htests/cache`,
	resolve: {
		alias: [
			workspace("@microsoft/kiota-abstractions", "packages/abstractions/src/index.ts"),
			workspace("@microsoft/kiota-serialization-json", "packages/serialization/json/src/index.ts"),
			workspace("@microsoft/kiota-serialization-text", "packages/serialization/text/src/index.ts"),
			workspace("@microsoft/kiota-serialization-form", "packages/serialization/form/src/index.ts"),
			workspace("@microsoft/kiota-serialization-multipart", "packages/serialization/multipart/src/index.ts"),
			workspace("@microsoft/kiota-authentication-azure", "packages/authentication/azure/src/index.ts"),
			workspace("@microsoft/kiota-authentication-spfx", "packages/authentication/spfx/src/index.ts"),
			{ find: /^@product\/fetch$/, replacement: `${ROOT}/packages/http/fetch/src/index.ts` },
		],
	},
	test: {
		include: [
			".htests/security/**/*.test.ts",
			".htests/functional/**/*.test.ts",
			"packages/http/fetch/test/node/RedirectHandler.ts",
			"packages/http/fetch/test/node/RedirectHandlerOptions.ts",
			"packages/http/fetch/test/node/kiotaClientFactory.ts",
			"packages/http/fetch/test/node/MiddlewareFactory.ts",
			"packages/http/fetch/test/node/httpClient.ts",
			"packages/http/fetch/test/common/middleware/authorizationHandler.ts",
			"packages/http/fetch/test/common/middleware/headersUtil.ts",
		],
		testTimeout: 30000,
		hookTimeout: 30000,
	},
});
