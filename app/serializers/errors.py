from typing import List

from pydantic import BaseModel


class ValidationErrorMessage(BaseModel):
    detail: dict[str, List[str]] = {"description": ["field required"]}


class SimpleErrorMessage(BaseModel):
    error_message: str = "error"
