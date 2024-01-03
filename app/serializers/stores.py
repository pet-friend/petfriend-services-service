from typing import List

from pydantic import BaseModel

from app.models.stores import StoreRead


class StoreList(BaseModel):
    stores: List[StoreRead]
    amount: int
