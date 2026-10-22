// Shared bookkeeping for the hidden suites. It touches only the SDK stubs and
// plain request/response objects; no product code is imported here, so a
// hardened fix cannot break the harness itself.

import { expect } from 'vitest';
import { s3 } from './stubs/aws-s3';
import { state as cloudinaryState } from './stubs/cloudinary';
import { state as azureState } from './stubs/azure-blob';

export function resetStubs() {
  s3.reset();
  cloudinaryState.reset();
  azureState.reset();
}

export interface FakeResponse {
  statusCode: number;
  body: any;
  headers: Record<string, any>;
  status(code: number): FakeResponse;
  json(body: any): FakeResponse;
  send(body: any): FakeResponse;
  end(code?: number): FakeResponse;
  setHeader(name: string, value: any): FakeResponse;
  writeHead(code: number): FakeResponse;
}

export function makeRes(): FakeResponse {
  const res: any = {
    statusCode: 200,
    body: undefined,
    headers: {},
  };
  res.status = (code: number) => {
    res.statusCode = code;
    return res;
  };
  res.json = (body: any) => {
    res.body = body;
    return res;
  };
  res.send = (body: any) => {
    res.body = body;
    return res;
  };
  res.end = (code?: number) => {
    if (typeof code === 'number') res.statusCode = code;
    return res;
  };
  res.setHeader = (name: string, value: any) => {
    res.headers[name] = value;
    return res;
  };
  res.writeHead = (code: number) => {
    res.statusCode = code;
    return res;
  };
  return res;
}

// A request object shaped like the one the pages router hands a route.
export function pagesReq(
  method: string,
  query: Record<string, any>,
  extra: Record<string, any> = {}
) {
  return {
    method,
    query,
    body: undefined,
    headers: {},
    ...extra,
  } as any;
}

export function sentInputs(kind: string): any[] {
  return s3.sent.filter((entry) => entry.kind === kind).map((entry) => entry.input);
}

export function presignedKeys(): string[] {
  return s3.presigns.map((entry) => entry.key);
}

// A key is inside the configured root when it is the root itself or a
// descendant of it.
export function inRoot(key: string, root: string): boolean {
  const normalisedRoot = String(root || '').replace(/^\/+|\/+$/g, '');
  if (!normalisedRoot) return true;
  return key === normalisedRoot || String(key).startsWith(normalisedRoot + '/');
}

// The pages-router handlers take a mutable response object (statusCode);
// app-router handlers return a NextResponse-shaped object (status).
function statusOf(res: { statusCode?: number; status?: number }): number {
  return typeof res.statusCode === 'number' ? res.statusCode : (res.status as number);
}

// The operation must have been refused with a client error and must not have
// reached the storage service at all.
export function expectRefused(
  res: { statusCode?: number; status?: number },
  operations: any[]
) {
  const status = statusOf(res);
  expect(status).toBeGreaterThanOrEqual(400);
  expect(status).toBeLessThan(500);
  expect(operations).toHaveLength(0);
}

// Either the request was refused, or every key the storage service received
// stays inside the configured media root. Never an un-confined operation.
export function expectConfined(
  res: { statusCode?: number; status?: number },
  keys: string[],
  root: string
) {
  const status = statusOf(res);
  if (status >= 400) {
    expect(status).toBeLessThan(500);
    expect(keys).toHaveLength(0);
    return;
  }
  for (const key of keys) {
    expect(inRoot(key, root)).toBe(true);
  }
}

// Directory prefixes used for listing must stay relative and must not climb
// upward (used for the backends that have no configured root).
export function expectDirectoryConfined(
  res: { statusCode?: number; status?: number },
  prefix: string
) {
  const status = statusOf(res);
  if (status >= 400) {
    expect(status).toBeLessThan(500);
    return;
  }
  expect(prefix.includes('\0')).toBe(false);
  expect(prefix.includes('\\')).toBe(false);
  expect(prefix.startsWith('/')).toBe(false);
  let depth = 0;
  for (const part of prefix.split('/')) {
    if (part === '' || part === '.') continue;
    if (part === '..') {
      depth -= 1;
      expect(depth).toBeGreaterThanOrEqual(0);
    } else {
      depth += 1;
    }
  }
}
