from typing import Sequence

from pydantic import BaseModel

from app.models.products import ProductRead


class ProductsList(BaseModel):
    products: Sequence[ProductRead]
    amount: int
