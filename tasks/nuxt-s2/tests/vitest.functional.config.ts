import { defineVitestProject } from '@nuxt/test-utils/config'
import { defineConfig } from 'vitest/config'

const defaultRules = {
  '/lower/case/**': { ssr: false },
  '/lower/exact': { redirect: '/target' },
  '/pre/**': { prerender: true },
  '/pre/spa/**': { prerender: true, ssr: false },
  '/data/feed': { cache: true },
  '/app/middleware': { appMiddleware: 'auth' },
  '/app/middleware-list': { appMiddleware: ['auth', 'audit'] },
  '/app/layout': { appLayout: 'custom' },
}

const sensitiveRules = {
  '/Admin/Dashboard': { appMiddleware: { auth: true } },
  '/lower/case': { ssr: false },
}

export default defineConfig({
  test: {
    fileParallelism: false,
    projects: [
      await defineVitestProject({
        test: {
          name: 'functional-default',
          dir: './.htests/functional/default',
          environment: 'nuxt',
          testTimeout: 120_000,
          hookTimeout: 120_000,
          environmentOptions: {
            nuxt: {
              overrides: {
                pages: true,
                routeRules: defaultRules,
                experimental: { appManifest: true },
              },
            },
          },
        },
      }),
      await defineVitestProject({
        test: {
          name: 'functional-sensitive',
          dir: './.htests/functional/sensitive',
          environment: 'nuxt',
          testTimeout: 120_000,
          hookTimeout: 120_000,
          environmentOptions: {
            nuxt: {
              overrides: {
                pages: true,
                routeRules: sensitiveRules,
                router: { options: { sensitive: true } },
                experimental: { appManifest: true },
              },
            },
          },
        },
      }),
      {
        test: {
          name: 'functional-project',
          dir: './.htests/functional/project',
          environment: 'node',
          testTimeout: 120_000,
        },
      },
      {
        test: {
          name: 'functional-server',
          dir: './.htests/functional/server',
          environment: 'node',
          testTimeout: 600_000,
          hookTimeout: 600_000,
        },
      },
    ],
  },
})
