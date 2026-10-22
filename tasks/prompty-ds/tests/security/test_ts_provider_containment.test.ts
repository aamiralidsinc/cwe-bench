/**
 * Author-named paths in a prompt document must stay inside its directory.
 *
 * Each case loads a document that names a harmless child prompt outside the
 * document's own directory and asks the provider package to project it, then
 * asserts that the projection refuses and never opens the outside file.
 */
import { describe, it, expect, vi } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const opened: string[] = [];

vi.mock("node:fs", async (importOriginal) => {
  const real = await importOriginal<typeof import("node:fs")>();
  return {
    ...real,
    readFileSync: ((path: any, options: any) => {
      try {
        opened.push(resolve(String(path)));
      } catch {
        opened.push(String(path));
      }
      return (real.readFileSync as any)(path, options);
    }) as typeof real.readFileSync,
  };
});

import { load } from "../src/core/loader.js";
import { buildChatArgs, buildResponsesArgs } from "../../openai/src/wire.js";

const OUTSIDE_MARKER = "PROMPTY-OUTSIDE-CONTENT-9f3a2c";

interface Tree {
  root: string;
  prompts: string;
  outsideChild: string;
}

function makeTree(): Tree {
  const root = mkdtempSync(join(tmpdir(), "prompty-ts-provider-"));
  const prompts = join(root, "prompts");
  mkdirSync(prompts);
  const outsideChild = join(root, "outside-child.prompty");
  writeFileSync(
    outsideChild,
    `---\nname: outside-child\nmodel: gpt-4\ndescription: ${OUTSIDE_MARKER}\n---\nchild body\n`,
  );
  symlinkSync(outsideChild, join(prompts, "escape-child.prompty"));
  return { root, prompts, outsideChild };
}

function writeParent(prompts: string, toolPath: string): string {
  const path = join(prompts, "parent.prompty");
  writeFileSync(
    path,
    "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
      + `    path: ${toolPath}\n---\nparent body\n`,
  );
  return path;
}

function expectNeverOpened(target: string): void {
  expect(opened, `an outside file was opened: ${target}`).not.toContain(resolve(target));
}

describe("child prompts projected by the provider package", () => {
  it("refuses a relative child outside the directory", () => {
    const t = makeTree();
    const parent = writeParent(t.prompts, "../outside-child.prompty");
    const agent = load(parent);
    opened.length = 0;
    expect(() => buildChatArgs(agent, [])).toThrow();
    expectNeverOpened(t.outsideChild);
  });

  it("refuses an absolute child path outside the directory", () => {
    const t = makeTree();
    const parent = writeParent(t.prompts, t.outsideChild);
    const agent = load(parent);
    opened.length = 0;
    expect(() => buildChatArgs(agent, [])).toThrow();
    expectNeverOpened(t.outsideChild);
  });

  it("refuses a link that points outside", () => {
    const t = makeTree();
    const parent = writeParent(t.prompts, "./escape-child.prompty");
    const agent = load(parent);
    opened.length = 0;
    expect(() => buildChatArgs(agent, [])).toThrow();
    expectNeverOpened(t.outsideChild);
  });

  it("refuses a relative child outside the directory for the responses format", () => {
    const t = makeTree();
    const parent = writeParent(t.prompts, "../outside-child.prompty");
    const agent = load(parent);
    opened.length = 0;
    expect(() => buildResponsesArgs(agent, [])).toThrow();
    expectNeverOpened(t.outsideChild);
  });
});
