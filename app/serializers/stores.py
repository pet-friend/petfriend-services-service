from typing import Sequence

from pydantic import BaseModel

from app.models.stores import StoreRead


class StoreList(BaseModel):
    stores: Sequence[StoreRead]
    amount: int
