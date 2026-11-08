"""Error handling. Every error the API returns has the same JSON shape:

    {"status": "error", "error_code": "...", "message": "..."}

so the frontend needs one handler, and `message` is always safe to show the user.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("eyecheck")


class ApiError(Exception):
    """Raised for problems the user can fix (bad file, blurry photo, ...)."""

    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


def _error(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "error_code": error_code, "message": message},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach the handlers to the app so they apply to every route."""

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        return _error(exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        # The common case is an upload without a "file" field; anything else is a generic bad request.
        # (`loc` is a tuple like ("body", "file").)
        if any(tuple(err.get("loc", ()))[-1:] == ("file",) for err in exc.errors()):
            return _error(422, "missing_file", "Please attach an image in the 'file' field.")
        return _error(422, "invalid_request", "The request was not in the expected format.")

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        # Log the details for us, but never send stack traces to the user.
        logger.exception("Unhandled error")
        return _error(500, "internal_error", "Something went wrong on our side. Please try again.")