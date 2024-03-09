from pydantic import BaseModel

from app.models.stores import StoreRead


class StoreList(BaseModel):
    stores: list[StoreRead]
    amount: int
