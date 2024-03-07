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
    messages_dict: dict[str, list[str]] = {}

    for error in exc.errors():
        if error["type"] == "json_invalid":
            field_name, char_no = error["loc"]
            error_msg = f'{error["msg"]}. {error["ctx"]["error"]} (at {field_name}.{char_no}).'
        else:
            field_name = error["loc"][-1]
            error_msg = error["msg"]
        messages_dict.setdefault(field_name, []).append(error_msg)
    json_schema = ValidatorSchema(detail=messages_dict).model_dump()
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=json_schema)


def handle_http_exception(_req: Request, exc: HTTPException) -> Response:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorSchema(error_message=exc.detail).model_dump(mode="json"),
    )
