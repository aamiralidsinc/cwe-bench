const noop = () => {}
module.exports = { createLogger: () => ({ info: noop, warn: noop, error: noop, debug: noop }), format: {}, transports: {} }
