export default defineNuxtConfig({
  ssr: true,
  pages: true,
  compatibilityDate: 'latest',
  future: { compatibilityVersion: 3 },
  typescript: { typeCheck: false },
  routeRules: {
    '/Admin/Dashboard': { prerender: true },
    '/Legacy/Home': { redirect: '/target' },
    '/Secret/Docs': { ssr: false },
  },
  nitro: { output: { dir: './.output' } },
})
