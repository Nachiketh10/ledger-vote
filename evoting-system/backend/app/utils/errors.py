"""
Common exception hierarchy for service-layer errors. Routes never need
to know the specific subclass — they (or the global error handler) just
read .message and .status. Keeping this in one place means every part
of the system (auth, elections, candidates, voting, fraud...) reports
errors the exact same way.
"""


class AppError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, 404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message, 403)


class ConflictError(AppError):
    def __init__(self, message: str = "This action conflicts with the current state."):
        super().__init__(message, 409)


class BadRequestError(AppError):
    def __init__(self, message: str = "Invalid request."):
        super().__init__(message, 400)
