// Runs before every test file: `require("electron")` from the product code gets the in-process
// stand-in (the real package only ships a launcher for the Electron binary).
import Module from "node:module"
import { fakeElectron } from "./fakeElectron"

// The product snapshots "is debug enabled" when its logger module loads; make that snapshot see
// the flag before any product module is imported. Tests that capture debug output rely on it.
process.env.DEBUG = process.env.DEBUG || "electron-builder"

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
