from pydantic import BaseModel


class ErrorSchema(BaseModel):
    error_message: str
