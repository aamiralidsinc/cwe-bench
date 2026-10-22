// Pristine verifier config. test.sh places it in the pristine runner copy
// (/opt/vitest-verifier, made when the image was built) and runs the hidden
// tests with that runner, so the agent's rebuild of the product cannot change
// how tests are collected or reported. Only the product surfaces under test
// are taken from /app: the runner API (`vitest/node`) and the preview browser
// provider. One group (security|functional) per run, selected by the VGROUP
// env var.
//
// Deliberately imports nothing, so loading it never resolves through /app.
const group = process.env.VGROUP || ''
const app = process.env.VERIFIER_APP || '/app'

export default {
  resolve: {
    alias: [
      { find: /^vitest\/node$/, replacement: `${app}/packages/vitest/dist/node.js` },
      { find: /^@vitest\/browser-preview$/, replacement: `${app}/packages/browser-preview/dist/index.js` },
    ],
  },
  test: {
    include: [`packages/vitest/__verifier__/${group}/**/*.test.ts`],
    pool: 'forks',
    fileParallelism: false,
    testTimeout: 30000,
    hookTimeout: 30000,
    cache: false,
  },
}
