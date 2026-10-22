// Runtime values of the enterprise interface module. The real module imports a
// schema-validation package that is not needed to exercise the request
// handlers; only the enums are exported here.
const ErrorMessage = {
    FORBIDDEN: 'Forbidden',
    UNAUTHORIZED: 'Unauthorized',
    NOT_FOUND: 'Not Found'
}

const UserStatus = {
    INVITED: 'invited',
    DISABLED: 'disabled',
    ACTIVE: 'active'
}

class LoggedInUser {}

module.exports = { ErrorMessage, UserStatus, LoggedInUser }
