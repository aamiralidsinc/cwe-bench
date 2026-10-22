/** Legitimate references inside a prompt's own directory must keep working. */
import { describe, it, expect, vi } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

vi.mock("../src/core/pipeline.js", () => ({
  prepare: vi.fn(async () => []),
  run: vi.fn(async () => "stub-run"),
  turn: vi.fn(async () => "stub-turn"),
}));

import { load } from "../src/core/loader.js";
import { dispatchTool } from "../src/core/tool-dispatch.js";
import { buildChatArgs, buildResponsesArgs } from "../../openai/src/wire.js";

function promptsDir(): string {
  const root = mkdtempSync(join(tmpdir(), "prompty-ts-ok-"));
  const prompts = join(root, "prompts");
  mkdirSync(prompts);
  writeFileSync(join(prompts, "inside.txt"), "INSIDE-TEXT-OK");
  mkdirSync(join(prompts, "frags"));
  writeFileSync(join(prompts, "frags", "desc.txt"), "SUBDIR-TEXT-OK");
  writeFileSync(
    join(prompts, "schema.json"),
    JSON.stringify([{ name: "question", kind: "string", default: "What is AI?" }]),
  );
  return prompts;
}

function writePrompt(prompts: string, name: string, text: string): string {
  const path = join(prompts, name);
  writeFileSync(path, text);
  return path;
}

describe("legitimate references", () => {
  it("returns a plain text reference", () => {
    const prompts = promptsDir();
    const prompt = writePrompt(
      prompts,
      "plain.prompty",
      '---\nname: plain\ndescription: "${file:inside.txt}"\n---\nbody\n',
    );
    expect(load(prompt).description).toBe("INSIDE-TEXT-OK");
  });

  it("returns a reference in a subdirectory", () => {
    const prompts = promptsDir();
    const prompt = writePrompt(
      prompts,
      "subdir.prompty",
      '---\nname: subdir\ndescription: "${file:frags/desc.txt}"\n---\nbody\n',
    );
    expect(load(prompt).description).toBe("SUBDIR-TEXT-OK");
  });

  it("accepts an absolute path inside the directory", () => {
    const prompts = promptsDir();
    const prompt = writePrompt(
      prompts,
      "absolute.prompty",
      `---\nname: absolute\ndescription: "\${file:${join(prompts, "inside.txt")}}"\n---\nbody\n`,
    );
    expect(load(prompt).description).toBe("INSIDE-TEXT-OK");
  });

  it("accepts an upward spelling that stays inside", () => {
    const prompts = promptsDir();
    const prompt = writePrompt(
      prompts,
      "normalized.prompty",
      '---\nname: normalized\ndescription: "${file:frags/../inside.txt}"\n---\nbody\n',
    );
    expect(load(prompt).description).toBe("INSIDE-TEXT-OK");
  });

  it("returns structured data for a structured target", () => {
    const prompts = promptsDir();
    const prompt = writePrompt(
      prompts,
      "structured.prompty",
      '---\nname: structured\ninputs: "${file:schema.json}"\n---\nbody\n',
    );
    expect(load(prompt).inputs[0].name).toBe("question");
    expect(load(prompt).inputs[0].default).toBe("What is AI?");
  });

  it("dispatches a child prompt inside the directory", async () => {
    const prompts = promptsDir();
    writeFileSync(
      join(prompts, "child.prompty"),
      "---\nname: child\nmodel: gpt-4\n---\nchild body\n",
    );
    const prompt = writePrompt(
      prompts,
      "parent.prompty",
      "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        + "    path: ./child.prompty\n---\nparent body\n",
    );
    const agent = load(prompt);
    expect(await dispatchTool("helper", {}, {}, agent, {})).toBe("stub-run");
  });

  it("projects a child prompt inside the directory through the provider wire format", () => {
    const prompts = promptsDir();
    writeFileSync(
      join(prompts, "child.prompty"),
      "---\nname: child\nmodel: gpt-4\ndescription: CHILD-DESC\n---\nchild body\n",
    );
    const prompt = writePrompt(
      prompts,
      "parent.prompty",
      "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        + "    path: ./child.prompty\n---\nparent body\n",
    );
    const agent = load(prompt);
    const args = buildChatArgs(agent, []);
    const fn = (args.tools as any)[0].function;
    expect(fn.name).toBe("helper");
    expect(fn.description).toBe("CHILD-DESC");
  });

  it("projects a child prompt inside the directory for the responses format", () => {
    const prompts = promptsDir();
    writeFileSync(
      join(prompts, "child.prompty"),
      "---\nname: child\nmodel: gpt-4\ndescription: CHILD-DESC\n---\nchild body\n",
    );
    const prompt = writePrompt(
      prompts,
      "parent.prompty",
      "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        + "    path: ./child.prompty\n---\nparent body\n",
    );
    const agent = load(prompt);
    const args = buildResponsesArgs(agent, []);
    const tool = (args.tools as any)[0];
    expect(tool.name).toBe("helper");
    expect(tool.description).toBe("CHILD-DESC");
  });
});
