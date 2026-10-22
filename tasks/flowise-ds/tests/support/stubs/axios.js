// Offline axios stub: no request leaves the process.
const reply = async () => ({ data: {} })
const axios = { post: reply, get: reply, isAxiosError: () => false }
module.exports = axios
module.exports.default = axios
