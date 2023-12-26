from pydantic import BaseModel


class ValidatorSchema(BaseModel):
    detail: dict[str, list[str]]
