from contextlib import asynccontextmanager
import logging
import os
import time
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from sqlalchemy.engine.base import Connection
from sqlalchemy.exc import IntegrityError
import uvicorn
from starlette.responses import JSONResponse
from alembic.config import Config
from alembic import command

from app.router import api_router
from app.validators.db_validator_schema import DatabaseValidatorSchema
from app.validators.validator_schema import ValidatorSchema
from .log import setup_logs
from .config import settings
from .db import engine

setup_logs()


@asynccontextmanager
async def run_migrations(_: FastAPI) -> AsyncIterator[None]:
    connection_attempt = 0
    while connection_attempt < 5:
        connection_attempt += 1
        logging.info(f"Attempting connection to database {connection_attempt}")
        try:

            def run(connection: Connection) -> None:
                alembic_cfg = Config("alembic.ini")
                alembic_cfg.attributes["connection"] = connection
                command.upgrade(alembic_cfg, "head")

            logging.info("Running migrations...")
            async with engine.begin() as conn:
                await conn.run_sync(run)
            logging.info("Migrations have been run")
            break
        except ConnectionRefusedError as exc:
            logging.info("Could not connect to database")
            if connection_attempt >= 5:
                logging.error("Max attempts reached, throwing error")
                raise exc
            time.sleep(10)
    yield


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
                    if "422" in responses:
                        del responses["422"]
    return app.openapi_schema


def create_app() -> FastAPI:
    logging.info("Starting...")
    new_app = FastAPI(title=settings.app_name, lifespan=run_migrations, debug=settings.DEBUG)
    new_app.include_router(api_router)
    new_app.openapi = custom_openapi  # type: ignore[method-assign]
    return new_app


app = create_app()
if __name__ == "__main__":
    reload = os.environ.get("ENVIRONMENT", None) == "DEVELOPMENT"
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", log_config=None, reload=reload, host=host, port=port)


@app.exception_handler(Exception)
def handle_exception(_req: Request, exc: Exception) -> Response:
    logging.error("Internal Server Error", exc_info=exc)
    return Response("Internal Server Error", status_code=500)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_req: Request, exc: RequestValidationError) -> JSONResponse:
    logging.error("Request Validation Error", exc_info=exc)
    messages_dict = {}
    for error in exc.errors():
        logging.info(error["loc"][-1])
        field_name = error["loc"][-1]
        if field_name not in messages_dict:
            messages_dict[field_name] = [error["msg"]]
        else:
            errors = messages_dict[field_name]
            errors.append(error["msg"])
    json_schema = ValidatorSchema(detail=messages_dict).model_dump(mode="json")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=json_schema)


@app.exception_handler(IntegrityError)
async def validation_integrity_error_handler(_req: Request, exc: IntegrityError) -> JSONResponse:
    logging.error("Request integrity Error", exc_info=exc)
    error_detail = DatabaseValidatorSchema(error=str(exc.orig)).get_error_detail(settings)
    json_schema = ValidatorSchema(detail=error_detail).model_dump(mode="json")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=json_schema)
