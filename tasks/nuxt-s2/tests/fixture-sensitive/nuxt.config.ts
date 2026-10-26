export default defineNuxtConfig({
  ssr: true,
  pages: true,
  compatibilityDate: 'latest',
  future: { compatibilityVersion: 3 },
  typescript: { typeCheck: false },
  router: { options: { sensitive: true } },
  routeRules: {
    '/Admin/Dashboard': { redirect: '/target' },
  },
  nitro: { output: { dir: './.output' } },
})
