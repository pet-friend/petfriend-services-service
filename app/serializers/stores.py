from typing import Sequence

from pydantic import BaseModel

from app.models.stores import StoreRead, ProductRead, Purchase, PurchaseRead


class StoreList(BaseModel):
    stores: Sequence[StoreRead]
    amount: int


class ProductsList(BaseModel):
    products: Sequence[ProductRead]
    amount: int


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
