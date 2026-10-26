import $ from "jquery";
import { loadHeader } from "../support/legacy";

describe("the account name shown in the page chrome", () => {
  it("keeps displaying an ordinary account name", () => {
    const { Header, Globals } = loadHeader();
    Globals.userLogedIn = { status: true, response: { userName: "Alice Example" } };
    const el = document.createElement("div");
    el.innerHTML = '<span class="userName"></span>';
    const view = { $: (sel: string) => $(el).find(sel), initializeGlobalSearch() {}, renderDownloadSearchResultview() {} };
    (Header as any).prototype.onRender.call(view);
    expect(el.querySelector(".userName")!.textContent).toBe("Alice Example");
  });
});
