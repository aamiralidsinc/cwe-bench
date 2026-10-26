import PropertiesTab from "@views/DetailPage/EntityDetailTabs/PropertiesTab/PropertiesTab";
import { renderAt, parse, executableMarkup } from "../support/dom";
import { tabState } from "../support/state";
import { XSS_ALL } from "../support/payloads";

describe("business metadata text values", () => {
  it("does not render authored markup as live HTML", () => {
    const state = tabState([{ name: "note", typeName: "string" }]);
    const entity = { typeName: "T", attributes: {}, businessAttributes: { bm: { note: XSS_ALL } } };
    const html = renderAt(<PropertiesTab entity={entity} referredEntities={{}} loading={false} />, state, "/detailPage/g1");
    expect(executableMarkup(parse(html))).toEqual([]);
  });
});
