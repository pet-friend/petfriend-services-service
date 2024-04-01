from typing import Sequence

from pydantic import BaseModel

from app.models.purchases import Purchase, PurchaseRead


class PurchaseList(BaseModel):
    purchases: Sequence[PurchaseRead]
    amount: int

    def __init__(self, purchases: Sequence[Purchase], amount: int):
        super().__init__(
            purchases=[
                PurchaseRead.model_validate(purchase.model_dump()) for purchase in purchases
            ],
            amount=amount,
        )
