from fastapi import Request
from fastapi.responses import Response

from app.exceptions.services import ServiceNotFound
from app.routes.responses.addresses import SERVICE_NOT_FOUND_ERROR
from .base_handlers import handle_http_exception


async def service_not_found_handler(req: Request, _exc: ServiceNotFound) -> Response:
    return handle_http_exception(req, SERVICE_NOT_FOUND_ERROR)
