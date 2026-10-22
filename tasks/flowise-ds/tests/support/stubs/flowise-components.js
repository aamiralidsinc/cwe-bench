module.exports = {
    getFileFromUpload: async () => Buffer.from(''),
    removeSpecificFileFromUpload: async () => {},
    streamStorageFile: async () => undefined,
    getFileFromStorage: async () => Buffer.from(''),
    addArrayFilesToStorage: async () => [],
    getFilesListFromStorage: async () => [],
    convertSchemaToZod: () => ({}),
    convertTextToSpeechStream: async () => {},
    getVoices: async () => [],
    ICommonObject: class {},
    EvaluationRunner: class {
        constructor() {}
        async runEvaluations() {
            return { rows: [] }
        }
    },
    MCPToolkit: class {},
    StorageProviderFactory: { getProvider: () => ({}) }
}
