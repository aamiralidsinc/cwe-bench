// Runs before every test file: `require("electron")` from the product code gets the in-process
// stand-in (the real package only ships a launcher for the Electron binary).
import Module from "node:module"
import { fakeElectron } from "./fakeElectron"

const mod = Module as any
if (!mod.__cweBenchElectronHook) {
  mod.__cweBenchElectronHook = true
  const load = mod._load
  mod._load = function (request: string, ...rest: Array<unknown>) {
    if (request === "electron") {
      return fakeElectron
    }
    return load.call(this, request, ...rest)
  }
}
