from fastapi import Request
from fastapi.responses import Response

from app.exceptions.addresses import AddressNotFound, AddressAlreadyExists
from app.routes.responses.addresses import ADDRESS_NOT_FOUND_ERROR, ADDRESS_EXISTS_ERROR
from .base_handlers import handle_http_exception


async def address_not_found_handler(req: Request, _exc: AddressNotFound) -> Response:
    return handle_http_exception(req, ADDRESS_NOT_FOUND_ERROR)


async def address_already_exists_handler(req: Request, _exc: AddressAlreadyExists) -> Response:
    return handle_http_exception(req, ADDRESS_EXISTS_ERROR)
