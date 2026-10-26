import PropertiesTab from "@views/DetailPage/EntityDetailTabs/PropertiesTab/PropertiesTab";
import { renderAt, parse, executableMarkup } from "../support/dom";
import { tabState } from "../support/state";
import { XSS_ALL } from "../support/payloads";

describe("business metadata list values", () => {
  it("does not render authored list items as live HTML", () => {
    const state = tabState([{ name: "labels", typeName: "array<string>" }]);
    const entity = { typeName: "T", attributes: {}, businessAttributes: { bm: { labels: [XSS_ALL, "plain"] } } };
    const html = renderAt(<PropertiesTab entity={entity} referredEntities={{}} loading={false} />, state, "/detailPage/g1");
    expect(executableMarkup(parse(html))).toEqual([]);
  });
});
