// Minimal stand-ins for the Nest primitives the driven API source imports.
class HttpException extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

class NotFoundException extends HttpException {
  constructor(message) {
    super(message, 404);
  }
}

class BadRequestException extends HttpException {
  constructor(message) {
    super(message, 400);
  }
}

const decorator = () => () => undefined;

module.exports = {
  Injectable: decorator,
  Inject: decorator,
  Optional: decorator,
  HttpException,
  NotFoundException,
  BadRequestException,
  Logger: class {},
  forwardRef: (value) => value,
};
