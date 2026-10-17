from flask import Flask
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException
from flask_limiter.errors import RateLimitExceeded

from app.utils.errors import AppError
from app.utils.responses import error


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return error("Validation failed.", 422, errors=err.messages)

    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return error(err.message, err.status)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(err):
        return error("Too many requests. Please try again shortly.", 429)

    @app.errorhandler(404)
    def handle_not_found(err):
        return error("Resource not found.", 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return error("Method not allowed.", 405)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        return error(err.description or "Request failed.", err.code or 400)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception("Unhandled exception")
        # Never leak internal error details/stack traces to the client.
        return error("An unexpected error occurred.", 500)
