// Pristine verifier config: runs the hidden tests against the SDK *source* in /app
// (no build step), resolving the workspace packages the same way the repo's own tests do.
import path from 'node:path';

import { defineConfig } from 'vitest/config';

const APP = process.env.MCP_APP_ROOT ?? '/app';
const pkg = rel => path.join(APP, 'packages', rel);

export default defineConfig({
    resolve: {
        alias: [
            { find: /^@modelcontextprotocol\/core-internal\/public$/, replacement: pkg('core-internal/src/exports/public/index.ts') },
            { find: /^@modelcontextprotocol\/core-internal\/validators\/ajv$/, replacement: pkg('core-internal/src/validators/ajvProvider.ts') },
            {
                find: /^@modelcontextprotocol\/core-internal\/validators\/cfWorker$/,
                replacement: pkg('core-internal/src/validators/cfWorkerProvider.ts')
            },
            { find: /^@modelcontextprotocol\/core-internal$/, replacement: pkg('core-internal/src/index.ts') },
            { find: /^@modelcontextprotocol\/core\/internal$/, replacement: pkg('core/src/internal.ts') },
            { find: /^@modelcontextprotocol\/core$/, replacement: pkg('core/src/index.ts') },
            { find: /^@modelcontextprotocol\/client\/_shims$/, replacement: pkg('client/src/shimsNode.ts') },
            { find: /^@modelcontextprotocol\/client\/validators\/ajv$/, replacement: pkg('client/src/validators/ajv.ts') },
            { find: /^@modelcontextprotocol\/client$/, replacement: pkg('client/src/index.ts') }
        ]
    },
    test: {
        environment: 'node',
        globals: false,
        testTimeout: 30_000,
        hookTimeout: 30_000,
        pool: 'forks',
        fileParallelism: false,
        cache: false
    }
});
