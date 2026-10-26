import { updateView } from "../support/legacy";
import { parse, executableMarkup } from "../support/dom";
import { XSS_ALL } from "../support/payloads";

const defs = [{ name: "note", typeName: "string" }, { name: "labels", typeName: "array<string>" }];

describe("rich-text business metadata in the search result table", () => {
  it("does not render a scalar authored value as live HTML", () => {
    const out = updateView({ note: XSS_ALL }, defs, { isEditorValue: true });
    expect(executableMarkup(parse(String(out)))).toEqual([]);
  });

  it("does not render authored list items as live HTML", () => {
    const out = updateView({ labels: [XSS_ALL, "ok"] }, defs, { isEditorValue: true });
    expect(executableMarkup(parse(String(out)))).toEqual([]);
  });
});
