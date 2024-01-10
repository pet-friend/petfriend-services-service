from fastapi import Request
from fastapi.responses import Response

from app.exceptions.stores import StoreNotFound, StoreAlreadyExists
from app.routes.responses.stores import STORE_NOT_FOUND_ERROR, STORE_EXISTS_ERROR
from .base_handlers import handle_http_exception


async def store_not_found_handler(req: Request, _exc: StoreNotFound) -> Response:
    return handle_http_exception(req, STORE_NOT_FOUND_ERROR)


async def store_already_exists_handler(req: Request, _exc: StoreAlreadyExists) -> Response:
    return handle_http_exception(req, STORE_EXISTS_ERROR)
