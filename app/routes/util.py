from typing import Any

from fastapi import HTTPException

from ..validators.error_schema import ErrorSchema


def get_exception_docs(*exceptions: HTTPException) -> dict[int | str, dict[str, Any]]:
    """
    Builds a dict of HTTP exceptions for the responses parameter of a FastAPI route.
    """
    return {e.status_code: {"model": ErrorSchema, "description": e.detail} for e in exceptions}
