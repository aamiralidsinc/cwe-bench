import $ from "jquery";
import { loadHeader } from "../support/legacy";
import { executableMarkup } from "../support/dom";
import { XSS_ALL } from "../support/payloads";

describe("the account name shown in the page chrome", () => {
  it("does not render the reported account name as live HTML", () => {
    const { Header, Globals } = loadHeader();
    Globals.userLogedIn = { status: true, response: { userName: XSS_ALL } };
    const el = document.createElement("div");
    el.innerHTML = '<span class="userName"></span>';
    const view = {
      $: (sel: string) => $(el).find(sel),
      initializeGlobalSearch() {},
      renderDownloadSearchResultview() {}
    };
    (Header as any).prototype.onRender.call(view);
    expect(executableMarkup(el)).toEqual([]);
  });
});
