from polyfactory.factories.pydantic_factory import ModelFactory

from app.models.addresses import AddressCreate


class AddressCreateFactory(ModelFactory[AddressCreate]):
    __model__ = AddressCreate
