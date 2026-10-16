// Runs once before the test files: ensure the data directories exist and create
// the account database schema by running the server's own migrations against
// the test database. Teardown reverses the migrations. Individual tests seed
// and clear their own rows.
import fs from 'node:fs';

import { config } from '@ss/load-config.js';
import { run as runMigrations } from '@ss/migrations.js';

export async function setup() {
  for (const key of ['serverFiles', 'userFiles']) {
    try {
      fs.mkdirSync(config.get(key), { recursive: true });
    } catch {
      /* ignore */
    }
  }
  await runMigrations('up');
}

export async function teardown() {
  try {
    await runMigrations('down');
  } catch {
    // ignore teardown errors
  }
}
