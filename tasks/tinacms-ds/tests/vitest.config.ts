import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = process.env.VERIFIER_APP || '/app';
const stub = (name: string) => path.join(HERE, 'support', 'stubs', name);

export default defineConfig({
  resolve: {
    alias: [
      { find: /^@app$/, replacement: APP },
      { find: /^@app\//, replacement: APP + '/' },
      { find: /^next\/server$/, replacement: stub('next-server.ts') },
      { find: /^next$/, replacement: stub('next.ts') },
      { find: /^@aws-sdk\/client-s3$/, replacement: stub('aws-s3.ts') },
      { find: /^@aws-sdk\/s3-request-presigner$/, replacement: stub('presigner.ts') },
      { find: /^@azure\/storage-blob$/, replacement: stub('azure-blob.ts') },
      { find: /^cloudinary$/, replacement: stub('cloudinary.ts') },
      { find: /^multer$/, replacement: stub('multer.ts') },
      { find: /^tinacms$/, replacement: stub('tinacms.ts') },
    ],
  },
  test: {
    include:
      process.env.VGROUP === 'functional'
        ? ['functional/**/*.test.ts']
        : ['security/**/*.test.ts'],
    environment: 'node',
    pool: 'forks',
    poolOptions: { forks: { singleFork: true } },
    testTimeout: 20000,
    hookTimeout: 20000,
  },
});
