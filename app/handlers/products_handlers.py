from fastapi import Request
from fastapi.responses import Response

from app.exceptions.products import ProductNotFound, ProductAlreadyExists
from app.routes.responses.products import PRODUCT_NOT_FOUND_ERROR, PRODUCT_EXISTS_ERROR
from .base_handlers import handle_http_exception


async def product_not_found_handler(req: Request, _exc: ProductNotFound) -> Response:
    return handle_http_exception(req, PRODUCT_NOT_FOUND_ERROR)


async def product_already_exists_handler(req: Request, _exc: ProductAlreadyExists) -> Response:
    return handle_http_exception(req, PRODUCT_EXISTS_ERROR)
