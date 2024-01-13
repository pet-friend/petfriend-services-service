from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.exceptions.addresses import AddressNotFound, AddressAlreadyExists
from app.exceptions.stores import StoreNotFound
from .base_handlers import handle_exception, validation_exception_handler, handle_http_exception
from .db_handlers import validation_integrity_error_handler
from .addresses_handlers import address_not_found_handler, address_already_exists_handler
from .stores_handlers import store_not_found_handler
from .image_handlers import file_exists_handler, file_not_found_handler


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, handle_exception)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(IntegrityError, validation_integrity_error_handler)
    app.add_exception_handler(AddressNotFound, address_not_found_handler)
    app.add_exception_handler(AddressAlreadyExists, address_already_exists_handler)
    app.add_exception_handler(StoreNotFound, store_not_found_handler)
    app.add_exception_handler(FileExistsError, file_exists_handler)
    app.add_exception_handler(FileNotFoundError, file_not_found_handler)
