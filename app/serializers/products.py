from pydantic import BaseModel

from app.models.products import ProductRead


class ProductsList(BaseModel):
    products: list[ProductRead]
    amount: int
