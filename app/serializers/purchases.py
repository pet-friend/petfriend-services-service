from typing import Sequence

from pydantic import BaseModel

from app.models.purchases import PurchaseRead


class PurchaseList(BaseModel):
    purchases: Sequence[PurchaseRead]
    amount: int
