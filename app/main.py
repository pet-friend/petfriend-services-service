import logging
import os
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import uvicorn


from app.handlers import add_exception_handlers
from app.router import api_router
from .log import setup_logs
from .config import settings
from .db import run_migrations

setup_logs()


def custom_openapi() -> dict[str, Any]:
    if not app.openapi_schema:
        app.openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        paths: Any | None = app.openapi_schema.get("paths")
        if paths is not None:
            items = paths.items()
            for _, method_item in items:
                for _, param in method_item.items():
                    responses = param.get("responses")
                    # remove 422 response, also can remove other status code
                    if "422" in responses and responses["422"]["description"] == "Validation Error":
                        del responses["422"]
    return app.openapi_schema


def create_app() -> FastAPI:
    logging.info("Starting...")
    new_app = FastAPI(title=settings.app_name, lifespan=run_migrations, debug=settings.DEBUG)
    new_app.include_router(api_router)
    new_app.openapi = custom_openapi  # type: ignore[method-assign]
    add_exception_handlers(new_app)
    return new_app


app = create_app()
if __name__ == "__main__":
    reload = os.environ.get("ENVIRONMENT", None) == "DEVELOPMENT"
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", log_config=None, reload=reload, host=host, port=port)
