from typing import Sequence

from pydantic import BaseModel

from app.models.stores import StoreRead, ProductRead, PurchaseRead


class StoreList(BaseModel):
    stores: Sequence[StoreRead]
    amount: int


class ProductsList(BaseModel):
    products: Sequence[ProductRead]
    amount: int


class PurchaseList(BaseModel):
    purchases: Sequence[PurchaseRead]
    amount: int
