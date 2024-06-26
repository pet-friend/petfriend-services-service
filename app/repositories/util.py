from typing import Any, Type
from math import radians, cos

from sqlmodel import func
from sqlalchemy import Exists, Function

from app.models.util import Coordinates

from ..models.stores import Store, Product
from ..models.services import Service
from ..models.addresses import Address


def distance_filter(
    model: Type[Store] | Type[Service], lat: float, long: float, less_than: float | Function[Any]
) -> Exists:
    """
    Based on https://stackoverflow.com/a/5207131
    Should be decently accurate for small distances (a few km)
    """

    km_per_deg_long = Coordinates.KM_PER_DEG_LAT * cos(radians(lat))
    return model.address.has(  # type: ignore
        func.pow(Coordinates.KM_PER_DEG_LAT * (Address.latitude - lat), 2)
        + func.pow(km_per_deg_long * (Address.longitude - long), 2)
        < func.pow(less_than, 2)
    )


def store_distance_filter(lat: float, long: float) -> Exists:
    return distance_filter(Store, lat, long, Store.delivery_range_km)


def product_distance_filter(lat: float, long: float) -> Exists:
    return Product.store.has(store_distance_filter(lat, long))  # type: ignore


def service_distance_filter(lat: float, long: float) -> Exists:
    return distance_filter(Service, lat, long, Service.customer_range_km)
