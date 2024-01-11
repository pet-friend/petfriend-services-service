from fastapi import Request
from fastapi.responses import Response

from app.routes.responses.image import IMAGE_EXISTS_ERROR, IMAGE_NOT_FOUND_ERROR
from .base_handlers import handle_http_exception


async def file_exists_handler(req: Request, _exc: FileExistsError) -> Response:
    return handle_http_exception(req, IMAGE_EXISTS_ERROR)


async def file_not_found_handler(req: Request, _exc: FileNotFoundError) -> Response:
    return handle_http_exception(req, IMAGE_NOT_FOUND_ERROR)
