// Offline stub for the server's utils barrel.
const decryptCredentialData = async (encrypted) => {
    const g = globalThis
    g.__decryptCalls = g.__decryptCalls || []
    g.__decryptCalls.push(encrypted)
    return { openAIApiKey: encrypted }
}
const encryptCredentialData = async (data) => JSON.stringify(data)
const getAppVersion = async () => '0.0.0'
const getRunningExpressApp = function () { return globalThis.__APPSERVER }
module.exports = { decryptCredentialData, encryptCredentialData, getAppVersion, getRunningExpressApp }
