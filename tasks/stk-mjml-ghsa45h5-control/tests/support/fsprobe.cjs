// Records filesystem reads made by a child process. Loaded with
// NODE_OPTIONS=--require so it runs before the product.
const fs = require('fs')
const log = process.env.FS_PROBE_LOG

if (log) {
  const record = target => {
    try {
      fs.appendFileSync(log, String(target) + '\n')
    } catch (e) {
      /* recording must never break the process under test */
    }
  }

  const readFileSync = fs.readFileSync
  fs.readFileSync = function (target, ...rest) {
    record(target)
    return readFileSync.call(this, target, ...rest)
  }

  const openSync = fs.openSync
  fs.openSync = function (target, ...rest) {
    record(target)
    return openSync.call(this, target, ...rest)
  }

  const readFile = fs.readFile
  fs.readFile = function (target, ...rest) {
    record(target)
    return readFile.call(this, target, ...rest)
  }

  const open = fs.open
  fs.open = function (target, ...rest) {
    record(target)
    return open.call(this, target, ...rest)
  }

  const createReadStream = fs.createReadStream
  fs.createReadStream = function (target, ...rest) {
    record(target)
    return createReadStream.call(this, target, ...rest)
  }
}
