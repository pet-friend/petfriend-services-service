import logging
from fastapi import Request, Response, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.validators.validator_schema import ValidatorSchema
from app.validators.error_schema import ErrorSchema


def handle_exception(_req: Request, exc: Exception) -> Response:
    logging.error("Internal Server Error", exc_info=exc)
    return handle_http_exception(
        _req,
        HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error"
        ),
    )


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
    json_schema = ValidatorSchema(detail=messages_dict).model_dump()
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=json_schema)


def handle_http_exception(_req: Request, exc: HTTPException) -> Response:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorSchema(error_message=exc.detail).model_dump(mode="json"),
    )
