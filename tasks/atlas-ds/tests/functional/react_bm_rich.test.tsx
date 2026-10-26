import PropertiesTab from "@views/DetailPage/EntityDetailTabs/PropertiesTab/PropertiesTab";
import { renderAt, parse, formattingPresent, executableMarkup } from "../support/dom";
import { tabState } from "../support/state";
import { RICH } from "../support/payloads";

describe("business metadata rich text", () => {
  it("keeps rendering the supported formatting and links", () => {
    const state = tabState([{ name: "note", typeName: "string" }, { name: "labels", typeName: "array<string>" }]);
    const entity = { typeName: "T", attributes: {}, businessAttributes: { bm: { note: RICH, labels: [RICH, "tail"] } } };
    const html = renderAt(<PropertiesTab entity={entity} referredEntities={{}} loading={false} />, state, "/detailPage/g1");
    const root = parse(html);
    expect(formattingPresent(root)).toBe(true);
    expect(executableMarkup(root)).toEqual([]);
  });
});
