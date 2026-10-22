const noop = () => {}
const logger = { info: noop, warn: noop, error: noop, debug: noop, verbose: noop, silly: noop }
module.exports = logger
module.exports.default = logger
