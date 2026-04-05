"""Custom exception hierarchy and FastAPI exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class SavvyException(Exception):
    """Base exception for all SavvyCore errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None, code: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        self.code = code or self.__class__.code
        super().__init__(self.detail)


class NotFoundError(SavvyException):
    status_code = 404
    code = "NOT_FOUND"
    detail = "The requested resource was not found."


class UnauthorizedError(SavvyException):
    status_code = 401
    code = "UNAUTHORIZED"
    detail = "Authentication is required."


class ForbiddenError(SavvyException):
    status_code = 403
    code = "FORBIDDEN"
    detail = "You do not have permission to perform this action."


class ConflictError(SavvyException):
    status_code = 409
    code = "CONFLICT"
    detail = "The request conflicts with the current state of the resource."


class ValidationError(SavvyException):
    status_code = 422
    code = "VALIDATION_ERROR"
    detail = "The request data is invalid."


async def savvy_exception_handler(_request: Request, exc: SavvyException) -> JSONResponse:
    """Handle all SavvyException subclasses with a consistent JSON envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred.", "code": "INTERNAL_ERROR"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""
    app.add_exception_handler(SavvyException, savvy_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)
