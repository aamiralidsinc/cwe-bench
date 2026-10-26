import DetailPageAttribute from "@views/DetailPage/DetailPageAttributes";
import { renderAt, parse, formattingPresent, executableMarkup } from "../support/dom";
import { tabState } from "../support/state";
import { RICH } from "../support/payloads";

describe("formatted descriptions", () => {
  it("keeps rendering the supported formatting and links", () => {
    const html = renderAt(
      <DetailPageAttribute data={{ name: "X", typeName: "T" }} description={RICH} subTypes={[]} superTypes={[]} loading={false} attributeDefs={[]} />,
      tabState([]), "/detailPage/g1?gtype=term"
    );
    const root = parse(html);
    expect(formattingPresent(root)).toBe(true);
    expect(executableMarkup(root)).toEqual([]);
  });
});
