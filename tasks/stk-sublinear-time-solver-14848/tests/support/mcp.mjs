// Minimal MCP client wiring for the two servers exercised by the hidden suites.
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './env.mjs';

async function connect(transport) {
  const client = new Client({ name: 'cwe-probe', version: '1.0.0' }, { capabilities: {} });
  await client.connect(transport);
  return client;
}

export async function connectConsciousness({ home, cwd, stateDir }) {
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [ROOT + '/.htests/support/ce-server.mjs'],
    cwd,
    env: { ...process.env, HOME: home, CONSCIOUSNESS_EXPLORER_STATE_DIR: stateDir },
  });
  return connect(transport);
}

export async function connectSolver({ home, cwd, vectorDir }) {
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [ROOT + '/dist/mcp/server.js'],
    cwd,
    env: { ...process.env, HOME: home, SUBLINEAR_SOLVER_VECTOR_DIR: vectorDir },
  });
  return connect(transport);
}

// A call is refused when the request fails OR the server answers with an error result.
// Everything else is a successful operation.
export async function assertRefused(promise, forbidden = [], label = '') {
  let text = '';
  let succeeded = false;
  try {
    const r = await promise;
    text = JSON.stringify(r);
    succeeded = !(r && r.isError);
  } catch (e) {
    text = String((e && e.message) || e);
  }
  assert.equal(succeeded, false, `${label}: the operation was accepted`);
  for (const marker of forbidden) {
    assert.equal(text.includes(String(marker)), false,
      `${label}: the refused response exposes ${marker}`);
  }
  return text;
}

export async function assertAlive(client, label = '') {
  const r = await client.callTool({ name: 'get_status', arguments: {} });
  assert.equal(r && r.isError ? true : false, false, `${label}: the server did not survive the refusal`);
}

// Find a regular file by name anywhere under `base` (the sandbox home/working
// tree), so the suites never assume the directory a fix chose for its data.
export function findFile(base, name) {
  const stack = [base];
  while (stack.length) {
    const dir = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) stack.push(full);
      else if (entry.isFile() && entry.name === name) return full;
    }
  }
  return null;
}

// Discover the directory an operation writes its data into: perform one
// legitimate save and look for the resulting file inside the sandbox.
export function dataDirOf(base, fileName) {
  const found = findFile(base, fileName);
  return found ? path.dirname(found) : null;
}
