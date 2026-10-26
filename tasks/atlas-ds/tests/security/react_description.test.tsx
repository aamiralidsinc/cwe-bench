import DetailPageAttribute from "@views/DetailPage/DetailPageAttributes";
import { renderAt, parse, executableMarkup } from "../support/dom";
import { tabState } from "../support/state";
import { XSS_ALL } from "../support/payloads";

describe("entity descriptions", () => {
  it("does not render an authored description as live HTML", () => {
    const html = renderAt(
      <DetailPageAttribute data={{ name: "X", typeName: "T" }} description={XSS_ALL} subTypes={[]} superTypes={[]} loading={false} attributeDefs={[]} />,
      tabState([]), "/detailPage/g1?gtype=term"
    );
    expect(executableMarkup(parse(html))).toEqual([]);
  });
});
