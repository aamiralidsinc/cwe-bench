const z = new Proxy(function () {}, { get: () => z, apply: () => z })
module.exports = { z, default: { z } }
