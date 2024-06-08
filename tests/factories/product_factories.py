from decimal import Decimal
from polyfactory.factories.pydantic_factory import ModelFactory

from app.models.stores import Category, ProductCreate


class ProductCreateFactory(ModelFactory[ProductCreate]):
    __model__ = ProductCreate

    name = "product name"
    categories = [Category(cat_str) for cat_str in ["alimentos", "juguetes", "higiene_y_cuidado"]]

    @classmethod
    def price(cls) -> Decimal:
        return Decimal(cls.__random__.uniform(1, 100)).quantize(Decimal("0.01"))
