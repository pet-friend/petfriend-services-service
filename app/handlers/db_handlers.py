import logging
from sqlalchemy.exc import IntegrityError
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.validators.db_validator_schema import DatabaseValidatorSchema
from app.validators.validator_schema import ValidatorSchema
from app.config import settings


async def validation_integrity_error_handler(_req: Request, exc: IntegrityError) -> JSONResponse:
    logging.error("Request integrity Error", exc_info=exc)
    error_detail = DatabaseValidatorSchema(error=str(exc.orig)).get_error_detail(settings)
    json_schema = ValidatorSchema(detail=error_detail).model_dump()
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=json_schema)
