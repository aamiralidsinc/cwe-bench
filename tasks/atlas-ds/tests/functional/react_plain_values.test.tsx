import PropertiesTab from "@views/DetailPage/EntityDetailTabs/PropertiesTab/PropertiesTab";
import { renderAt, parse } from "../support/dom";
import { tabState } from "../support/state";

describe("plain business metadata values", () => {
  it("keeps showing the same visible text", () => {
    const state = tabState([{ name: "note", typeName: "string" }, { name: "labels", typeName: "array<string>" }]);
    const entity = { typeName: "T", attributes: {}, businessAttributes: { bm: { note: "a & b", labels: ["one", "two"] } } };
    const root = parse(renderAt(<PropertiesTab entity={entity} referredEntities={{}} loading={false} />, state, "/detailPage/g1"));
    expect(root.textContent).toContain("a & b");
    expect(root.textContent).toContain("one, two");
  });
});
