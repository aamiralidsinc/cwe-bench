import { updateView } from "../support/legacy";
import { parse, formattingPresent, executableMarkup } from "../support/dom";
import { RICH } from "../support/payloads";

const defs = [{ name: "note", typeName: "string" }, { name: "labels", typeName: "array<string>" }];

describe("legacy rich-text business metadata", () => {
  it("keeps rendering supported formatting for scalar and list values", () => {
    const scalar = parse(String(updateView({ note: RICH }, defs, { isEditorValue: true })));
    expect(formattingPresent(scalar)).toBe(true);
    expect(executableMarkup(scalar)).toEqual([]);
    const list = parse(String(updateView({ labels: [RICH, "tail"] }, defs, { isEditorValue: true })));
    expect(formattingPresent(list)).toBe(true);
    expect(executableMarkup(list)).toEqual([]);
  });
});
