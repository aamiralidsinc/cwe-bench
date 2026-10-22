/**
 * Author-named paths in a prompt document must stay inside its directory.
 *
 * Each case loads (or uses) a document that names a harmless marker file
 * outside the document's own directory, and asserts that the library refuses
 * and never opens the outside file — whichever part of the document names the
 * path, however the path is spelled, and whichever public entry point is used.
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

// Child prompts execute through the pipeline; stub it so a dispatch test never
// leaves the process or touches a provider.
vi.mock("../src/core/pipeline.js", () => ({
  prepare: vi.fn(async () => []),
  run: vi.fn(async () => "stub-run"),
  turn: vi.fn(async () => "stub-turn"),
}));

import { load } from "../src/core/loader.js";
import { dispatchTool } from "../src/core/tool-dispatch.js";

const OUTSIDE_MARKER = "PROMPTY-OUTSIDE-CONTENT-9f3a2c";

interface Tree {
  root: string;
  prompts: string;
  outside: string;
  outsideChild: string;
}

function makeTree(): Tree {
  const root = mkdtempSync(join(tmpdir(), "prompty-ts-"));
  const prompts = join(root, "prompts");
  mkdirSync(prompts);
  const outside = join(root, "outside-content.txt");
  writeFileSync(outside, OUTSIDE_MARKER);
  const outsideChild = join(root, "outside-child.prompty");
  writeFileSync(
    outsideChild,
    `---\nname: outside-child\nmodel: gpt-4\ndescription: ${OUTSIDE_MARKER}\n---\nchild body\n`,
  );
  symlinkSync(outside, join(prompts, "escape-file.txt"));
  return { root, prompts, outside, outsideChild };
}

function writePrompt(prompts: string, name: string, text: string): string {
  const path = join(prompts, name);
  writeFileSync(path, text);
  return path;
}

function expectNeverOpened(target: string): void {
  expect(opened, `an outside file was opened: ${target}`).not.toContain(resolve(target));
}

describe("file references in frontmatter", () => {
  it("refuses a relative traversal", () => {
    const t = makeTree();
    const prompt = writePrompt(
      t.prompts,
      "attack.prompty",
      '---\nname: attack\ndescription: "${file:../outside-content.txt}"\n---\nbody\n',
    );
    opened.length = 0;
    expect(() => load(prompt)).toThrow();
    expectNeverOpened(t.outside);
  });

  it("refuses an absolute path", () => {
    const t = makeTree();
    const prompt = writePrompt(
      t.prompts,
      "attack.prompty",
      `---\nname: attack\ndescription: "\${file:${t.outside}}"\n---\nbody\n`,
    );
    opened.length = 0;
    expect(() => load(prompt)).toThrow();
    expectNeverOpened(t.outside);
  });

  it("refuses a link that points outside", () => {
    const t = makeTree();
    const prompt = writePrompt(
      t.prompts,
      "attack.prompty",
      '---\nname: attack\ndescription: "${file:escape-file.txt}"\n---\nbody\n',
    );
    opened.length = 0;
    expect(() => load(prompt)).toThrow();
    expectNeverOpened(t.outside);
  });

  it("refuses a reference nested in a pulled-in file", () => {
    const t = makeTree();
    writeFileSync(
      join(t.prompts, "model.json"),
      '{"id": "${file:../outside-content.txt}", "provider": "openai"}',
    );
    const prompt = writePrompt(
      t.prompts,
      "attack.prompty",
      '---\nname: attack\nmodel: "${file:model.json}"\n---\nbody\n',
    );
    opened.length = 0;
    expect(() => load(prompt)).toThrow();
    expectNeverOpened(t.outside);
  });
});

describe("child prompts declared as tools", () => {
  it("refuses a relative child outside the directory", async () => {
    const t = makeTree();
    const prompt = writePrompt(
      t.prompts,
      "parent.prompty",
      "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        + "    path: ../outside-child.prompty\n---\nparent body\n",
    );
    const agent = load(prompt);
    opened.length = 0;
    const result = await dispatchTool("helper", {}, {}, agent, {});
    expectNeverOpened(t.outsideChild);
    expect(result).not.toContain(OUTSIDE_MARKER);
  });

  it("refuses an absolute child path outside the directory", async () => {
    const t = makeTree();
    const prompt = writePrompt(
      t.prompts,
      "parent.prompty",
      "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n" +
        `    path: ${t.outsideChild}\n---\nparent body\n`,
    );
    const agent = load(prompt);
    opened.length = 0;
    const result = await dispatchTool("helper", {}, {}, agent, {});
    expectNeverOpened(t.outsideChild);
    expect(result).not.toContain(OUTSIDE_MARKER);
  });
});
