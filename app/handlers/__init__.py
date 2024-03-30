from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from .default import add_default_handlers
from .base_handlers import handle_exception, validation_exception_handler, handle_http_exception
from .db_handlers import validation_integrity_error_handler


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, handle_exception)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(IntegrityError, validation_integrity_error_handler)
    add_default_handlers(app)
