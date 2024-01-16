from polyfactory.factories.pydantic_factory import ModelFactory

from app.models.products import ProductCreate


class ProductCreateFactory(ModelFactory[ProductCreate]):
    __model__ = ProductCreate
