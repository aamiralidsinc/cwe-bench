/**
 * Functional tests for the other language runtime: ordinary in-directory
 * references keep working exactly as before, and structured references still
 * return structured data.
 */
import { describe, it, expect } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { load } from "/app/runtime/typescript/packages/core/src/core/loader.js";

function scaffold() {
  const root = mkdtempSync(join(tmpdir(), "ts-fun-"));
  const promptDir = join(root, "prompts");
  mkdirSync(promptDir);
  return { root, promptDir };
}

describe("in-directory references keep working", () => {
  it("returns structured data for a structured reference beside the prompt", () => {
    const { promptDir } = scaffold();
    writeFileSync(
      join(promptDir, "shared_connection.json"),
      JSON.stringify({
        kind: "key",
        endpoint: "https://shared.example/",
        apiKey: "shared-key",
      }),
    );
    const p = join(promptDir, "a.prompty");
    writeFileSync(
      p,
      "---\n" +
        "name: a\n" +
        "model:\n  id: gpt-4\n  apiType: chat\n  connection: ${file:shared_connection.json}\n" +
        "---\n" +
        "Hello\n",
    );
    const agent = load(p) as unknown as {
      model?: { connection?: { kind?: string; endpoint?: string } };
    };
    const conn = agent.model?.connection;
    expect(conn).toBeTruthy();
    expect(conn?.kind).toBe("key");
    expect(conn?.endpoint).toBe("https://shared.example/");
  });

  it("inlines a reference into a sub-directory of the prompt directory", () => {
    const { promptDir } = scaffold();
    mkdirSync(join(promptDir, "frags"));
    writeFileSync(join(promptDir, "frags", "desc.txt"), "subdir description");
    const p = join(promptDir, "b.prompty");
    writeFileSync(
      p,
      '---\nname: b\ndescription: "${file:frags/desc.txt}"\n---\nHello\n',
    );
    const agent = load(p) as unknown as { description?: string };
    expect(agent.description).toBe("subdir description");
  });
});
