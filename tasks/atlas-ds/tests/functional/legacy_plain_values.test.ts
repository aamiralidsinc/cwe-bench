import { updateView } from "../support/legacy";
import { parse } from "../support/dom";

const defs = [{ name: "note", typeName: "string" }, { name: "labels", typeName: "array<string>" }, { name: "count", typeName: "int" }];

describe("legacy plain values", () => {
  it("keeps escaping ordinary values and showing their text", () => {
    const out = String(updateView({ note: "a < b & c" }, defs, {}));
    expect(out).toContain("&lt;");
    expect(parse(out).textContent).toContain("a < b & c");
  });
  it("keeps joining list values and showing numbers", () => {
    const out = String(updateView({ labels: ["one", "two"], count: 7 }, defs, {}));
    const text = parse(out).textContent || "";
    expect(text).toContain("one, two");
    expect(text).toContain("7");
  });
});
