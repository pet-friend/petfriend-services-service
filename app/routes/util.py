from typing import Any, Type

from fastapi import HTTPException, UploadFile

from app.routes.responses.image import INVALID_IMAGE_ERROR

from ..validators.error_schema import ErrorSchema


def get_exception_docs(
    *exceptions: HTTPException | tuple[Type[Exception], HTTPException]
) -> dict[int | str, dict[str, Any]]:
    """
    Builds a dict of HTTP exceptions for the responses parameter of a FastAPI route.
    """
    docs: dict[int | str, dict[str, Any]] = {}
    for exc in exceptions:
        if isinstance(exc, tuple):
            _, exc = exc
        docs[exc.status_code] = {"model": ErrorSchema, "description": exc.detail}
    return docs


def get_image(image: UploadFile) -> UploadFile:
    """
    Validates that the uploaded file is an image, and raises an exception otherwise.
    """
    if not (image.content_type and image.content_type.startswith("image/")):
        raise INVALID_IMAGE_ERROR
    return image


def process_list(data: list[Any] | str) -> list[Any]:
    """
    Converts a string to a list of strings, or returns the list as is.
    """
    return data.split(",") if isinstance(data, str) else data
