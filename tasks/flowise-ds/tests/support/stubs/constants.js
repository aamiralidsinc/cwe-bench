// Offline stub of the server constants module (the real one imports every SSO
// provider class). Only the values the tested modules read are provided.
module.exports = {
    WHITELIST_URLS: [],
    INPUT_PARAMS_TYPE: ['string', 'number', 'boolean', 'options', 'multiOptions', 'code', 'json', 'credential'],
    GeneralErrorMessage: {
        FORBIDDEN: 'Forbidden',
        UNAUTHORIZED: 'Unauthorized',
        UNHANDLED_EDGE_CASE: 'Unhandled Edge Case',
        INVALID_PASSWORD: 'Invalid Password',
        NOT_ALLOWED_TO_DELETE_OWNER: 'Not Allowed To Delete Owner',
        INTERNAL_SERVER_ERROR: 'Internal Server Error',
        SMTP_NOT_CONFIGURED: 'Email (SMTP) is not configured on this server'
    },
    GeneralSuccessMessage: {
        CREATED: 'Created',
        UPDATED: 'Updated',
        DELETED: 'Deleted'
    }
}
