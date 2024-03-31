from decimal import Context, Decimal
from polyfactory.factories.pydantic_factory import ModelFactory
from app.models.constants.stores import MAX_DELIVERY_RANGE, MIN_DELIVERY_RANGE

from app.models.stores import StoreCreate


class StoreCreateFactory(ModelFactory[StoreCreate]):
    __model__ = StoreCreate

    @classmethod
    def delivery_range_km(cls) -> float:
        return cls.__random__.uniform(MIN_DELIVERY_RANGE, MAX_DELIVERY_RANGE)

    @classmethod
    def shipping_cost(cls) -> Decimal:
        return Context(prec=2).create_decimal_from_float(cls.__random__.uniform(0, 100))
