import fs from "fs";
import vm from "vm";
import path from "path";
import $ from "jquery";
import _ from "underscore";
import moment from "moment";
import momentTimezone from "moment-timezone";
import createDOMPurify from "dompurify";

export const ATLAS: string = (globalThis as any).process?.env?.ATLAS_ROOT || "/workspace";
const JS = path.join(ATLAS, "dashboardv2/public/js");

type Mod = { deps: any[]; factory: (...a: any[]) => any };

function run(file: string): Mod {
  const g: any = globalThis as any;
  let captured: Mod | null = null;
  g.define = (deps: any, factory: any) => { captured = { deps, factory }; };
  vm.runInThisContext(fs.readFileSync(file, "utf8"), { filename: file });
  if (!captured) throw new Error("module did not call define: " + file);
  return captured;
}

export interface Legacy {
  Utils: any;
  Enums: any;
  CVF: any;
  Globals: any;
  $: any;
  _: any;
}

let cached: Legacy | null = null;

export function legacy(): Legacy {
  if (cached) return cached;
  const g: any = globalThis as any;
  g.window = (globalThis as any).window;
  g.$ = $; g.jQuery = $; g._ = _;
  const DOMPurify = createDOMPurify(g.window);
  const Globals: any = { userLogedIn: { status: false, response: {} }, isDebugMetricsEnabled: false, saveApplicationState: { tabState: {} } };
  const Messages: any = { defaultErrorMessage: "unexpected error", deleteErrorMessage: " delete failed", getAbbreviationMsg: () => "" };
  const Modal: any = function () {};
  function PNotify() {}
  (PNotify as any).prototype.options = {};
  const store: any = { get: () => null, set: () => {} };
  const Enums = run(path.join(JS, "utils/Enums.js")).factory(() => {}, {});
  const Utils = run(path.join(JS, "utils/Utils.js"))
    .factory(() => {}, Globals, PNotify, Messages, Enums, moment, store, Modal, DOMPurify);
  const CVF = run(path.join(JS, "utils/CommonViewFunction.js"))
    .factory(() => {}, Utils, Modal, Messages, Enums, moment, Globals, momentTimezone);
  cached = { Utils, Enums, CVF, Globals, $, _ };
  return cached;
}

export function loadHeader(): any {
  const g: any = globalThis as any;
  g.$ = $; g.jQuery = $; g._ = _;
  class View {}
  (View as any).extend = function (proto: any) {
    function C() {}
    (C as any).prototype = Object.assign(Object.create(View.prototype), proto);
    return C;
  };
  g.Marionette = { LayoutView: View };
  const m = run(path.join(JS, "views/site/Header.js"));
  const Globals = { userLogedIn: { status: false, response: {} }, isDebugMetricsEnabled: false };
  const UrlLinks: any = {};
  return { Header: m.factory(() => {}, {}, {}, Globals, {}, UrlLinks, {}), Globals };
}

export function updateView(valueObject: any, attributeDefs: any[], extra: any = {}) {
  const { CVF } = legacy();
  return CVF.propertyTable({
    scope: {},
    valueObject,
    attributeDefs,
    isTable: false,
    numberFormat: (n: any) => String(n),
    ...extra
  });
}
