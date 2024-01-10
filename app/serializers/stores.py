from typing import List

from pydantic import BaseModel

from app.models.stores import StoreReadWithImage


class StoreList(BaseModel):
    stores: List[StoreReadWithImage]
    amount: int
