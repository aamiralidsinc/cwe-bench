// Offline stub of the server's utils barrel. Decryption records the ciphertext
// it was asked to decrypt and returns a plain data object shaped like the
// credentials used by the tested features.
const decryptCredentialData = async (encrypted) => {
    const g = globalThis
    g.__decryptCalls = g.__decryptCalls || []
    g.__decryptCalls.push(encrypted)
    return {
        openAIApiKey: encrypted,
        clientId: `client-${encrypted}`,
        clientSecret: `client-secret-${encrypted}`,
        authorizationUrl: 'https://auth.example.invalid/authorize',
        accessTokenUrl: 'https://auth.example.invalid/token'
    }
}

const encryptCredentialData = async (data) => JSON.stringify(data)
const getAppVersion = async () => '0.0.0'
const transformToCredentialEntity = (body) => ({ ...body })
const generateId = () => 'id_' + Math.random().toString(36).slice(2)
const getMulterStorage = () => ({
    array: () => (req, res, next) => next(),
    single: () => (req, res, next) => next(),
    any: () => (req, res, next) => next()
})
const databaseEntities = []

module.exports = {
    decryptCredentialData,
    encryptCredentialData,
    getAppVersion,
    transformToCredentialEntity,
    generateId,
    getMulterStorage,
    databaseEntities
}
