/**
 * Security tests for the other language runtime this repository ships: a path
 * a prompt document expresses must never read a file outside the prompt's own
 * directory.
 *
 * Each test writes a secret file outside the prompt directory, marks it with a
 * random token, drives the runtime's public load call, and asserts the attack
 * is blocked: loading either throws (no file is read) or returns a prompt that
 * does not carry the secret token.
 */
import { describe, it, expect } from "vitest";
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  symlinkSync,
} from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { randomBytes } from "node:crypto";
// The agent's tree is /app at grading time; resolve the product from there.
import { load } from "/app/runtime/typescript/packages/core/src/core/loader.js";

function token(): string {
  return "SEC_" + randomBytes(8).toString("hex");
}

function blob(agent: unknown): string {
  try {
    return JSON.stringify(agent, (_k, v) => (v instanceof Error ? String(v) : v));
  } catch {
    return String(agent);
  }
}

function assertBlocked(tok: string, call: () => unknown): void {
  let result: unknown;
  try {
    result = call();
  } catch {
    return; // refused before reading — acceptable
  }
  expect(blob(result)).not.toContain(tok);
}

function scaffold() {
  const root = mkdtempSync(join(tmpdir(), "ts-sec-"));
  const promptDir = join(root, "prompts");
  mkdirSync(promptDir);
  return { root, promptDir };
}

describe("document file references stay inside the prompt directory", () => {
  it("refuses a relative path that walks upward", () => {
    const tok = token();
    const { root, promptDir } = scaffold();
    writeFileSync(join(root, "secret.txt"), tok);
    const p = join(promptDir, "a.prompty");
    writeFileSync(
      p,
      `---\nname: a\ndescription: "\${file:../secret.txt}"\n---\nHi\n`,
    );
    assertBlocked(tok, () => blob(load(p)));
  });

  it("refuses an absolute path outside the prompt directory", () => {
    const tok = token();
    const { root, promptDir } = scaffold();
    const secret = join(root, "secret.txt");
    writeFileSync(secret, tok);
    const p = join(promptDir, "b.prompty");
    writeFileSync(
      p,
      `---\nname: b\ndescription: "\${file:${secret}}"\n---\nHi\n`,
    );
    assertBlocked(tok, () => blob(load(p)));
  });

  it("refuses a link inside the prompt directory that points outward", () => {
    const tok = token();
    const { root, promptDir } = scaffold();
    const secret = join(root, "secret.txt");
    writeFileSync(secret, tok);
    try {
      symlinkSync(secret, join(promptDir, "link.txt"));
    } catch {
      return; // symlinks unavailable — nothing to assert
    }
    const p = join(promptDir, "c.prompty");
    writeFileSync(
      p,
      `---\nname: c\ndescription: "\${file:link.txt}"\n---\nHi\n`,
    );
    assertBlocked(tok, () => blob(load(p)));
  });
});
