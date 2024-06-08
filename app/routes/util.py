from typing import Any, Type

from fastapi import HTTPException, UploadFile
import filetype  # type: ignore

from .responses.image import INVALID_IMAGE_ERROR
from ..validators.error_schema import ErrorSchema


def get_exception_docs(
    *exceptions: HTTPException | tuple[Type[Exception], HTTPException]
) -> dict[int | str, dict[str, Any]]:
    """
    Builds a dict of HTTP exceptions for the responses parameter of a FastAPI route.
    """
    by_status_code: dict[int, list[HTTPException]] = {}
    for exc in exceptions:
        if isinstance(exc, tuple):
            exc = exc[1]
        by_status_code.setdefault(exc.status_code, []).append(exc)

    docs: dict[int | str, dict[str, Any]] = {}
    for status, exc_list in by_status_code.items():
        docs[status] = {
            "model": ErrorSchema,
            "description": " || ".join(e.detail for e in exc_list),
        }
    return docs


def get_image(image: UploadFile) -> UploadFile:
    """
    Validates that the uploaded file is an image, and raises an exception otherwise.
    """
    content_type: str | None = filetype.guess_mime(image.file)
    if not (content_type and content_type.startswith("image/")):
        raise INVALID_IMAGE_ERROR
    return image


def process_list(data: list[Any] | str) -> list[Any]:
    """
    Converts a string to a list of strings, or returns the list as is.
    """
    return data.split(",") if isinstance(data, str) else data
