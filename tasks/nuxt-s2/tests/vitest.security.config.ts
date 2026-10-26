import { defineVitestProject } from '@nuxt/test-utils/config'
import { defineConfig } from 'vitest/config'

const defaultRules = {
  '/Admin/Dashboard': { appMiddleware: { auth: true } },
  '/Secret/Docs/**': { ssr: false, appMiddleware: ['auth'] },
  '/Legacy/Home': { redirect: '/target' },
  '/Data/Feed': { cache: true },
  '/lower/case/**': { ssr: false },
}

const sensitiveRules = {
  '/Admin/Dashboard': { appMiddleware: { auth: true }, prerender: true },
  '/legacy/home': { ssr: false },
}

export default defineConfig({
  test: {
    fileParallelism: false,
    projects: [
      await defineVitestProject({
        test: {
          name: 'security-default',
          dir: './.htests/security/default',
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
          name: 'security-sensitive',
          dir: './.htests/security/sensitive',
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
          name: 'security-server',
          dir: './.htests/security/server',
          environment: 'node',
          testTimeout: 600_000,
          hookTimeout: 600_000,
        },
      },
    ],
  },
})
