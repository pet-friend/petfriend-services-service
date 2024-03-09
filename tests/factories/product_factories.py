from polyfactory.factories.pydantic_factory import ModelFactory

from app.models.products import Category, ProductCreate


class ProductCreateFactory(ModelFactory[ProductCreate]):
    __model__ = ProductCreate

    name = "product name"
    categories = [Category(cat_str) for cat_str in ["alimentos", "juguetes", "higiene_y_cuidado"]]
