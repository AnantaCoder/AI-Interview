from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.schemas.responses import ErrorResponse
from app.config.logging import get_logger

logger = get_logger("exceptions.handlers")


class AppException(Exception):
    def __init__(self, message: str, error_code: str = None, status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(message, error_code, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", error_code: str = "UNAUTHORIZED"):
        super().__init__(message, error_code, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", error_code: str = "FORBIDDEN"):
        super().__init__(message, error_code, status_code=403)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict", error_code: str = "CONFLICT"):
        super().__init__(message, error_code, status_code=409)


def register_exception_handlers(app: FastAPI) -> None:
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(f"App exception: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=exc.message,
                error_code=exc.error_code
            ).model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(f"HTTP exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=str(exc.detail),
                error_code="HTTP_ERROR"
            ).model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Validation error: {exc.errors()}")
        errors = exc.errors()
        details = {
            "fields": [
                {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
                for err in errors
            ]
        }
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                message="Validation failed",
                error_code="VALIDATION_ERROR",
                details=details
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="Internal server error",
                error_code="INTERNAL_ERROR"
            ).model_dump()
        )
