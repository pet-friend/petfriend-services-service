from fastapi import Request
from fastapi.responses import Response

from app.exceptions.addresses import AddressNotFound, NonExistentAddress
from app.routes.responses.addresses import (
    ADDRESS_NOT_FOUND_ERROR,
    NON_EXISTENT_ADDRESS_ERROR,
)
from .base_handlers import handle_http_exception


async def address_not_found_handler(req: Request, _exc: AddressNotFound) -> Response:
    return handle_http_exception(req, ADDRESS_NOT_FOUND_ERROR)


async def non_existent_address_handler(req: Request, _exc: NonExistentAddress) -> Response:
    return handle_http_exception(req, NON_EXISTENT_ADDRESS_ERROR)
