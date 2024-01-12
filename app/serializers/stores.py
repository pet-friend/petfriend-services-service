from typing import List

from pydantic import BaseModel

from app.models.stores import StoreReadWithImage


class StoreList(BaseModel):
    stores: list[StoreReadWithImage]
    amount: int
