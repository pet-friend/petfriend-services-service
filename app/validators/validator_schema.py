from pydantic import BaseModel


class ValidatorSchema(BaseModel):
    detail: dict[str | int, list[str]]
