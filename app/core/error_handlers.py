import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger("app.errors")

HTTP_ERROR_MESSAGES = {
    404: "Recurso no encontrado",
    405: "Método no permitido",
}


def error_body(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", "Datos inválidos", details),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=error_body(
                "conflict",
                "El recurso entra en conflicto con datos existentes",
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code = {
            404: "not_found",
            405: "method_not_allowed",
        }.get(exc.status_code, "http_error")
        message = HTTP_ERROR_MESSAGES.get(exc.status_code, str(exc.detail))
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, message),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_body("internal_error", "Error interno del servidor"),
        )
