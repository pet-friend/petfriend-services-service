from fastapi import Request
from fastapi.responses import Response

from app.routes.responses.auth import FORBIDDEN
from app.exceptions.users import Forbidden
from .base_handlers import handle_http_exception


async def forbidden_handler(req: Request, _exc: Forbidden) -> Response:
    return handle_http_exception(req, FORBIDDEN)
