from typing import Any, Type
from math import radians, cos

from sqlmodel import func
from sqlalchemy import Exists, Function

from app.models.util import KM_PER_DEG_LAT

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

    km_per_deg_long = KM_PER_DEG_LAT * cos(radians(lat))
    return model.address.has(  # type: ignore
        func.pow(KM_PER_DEG_LAT * (Address.latitude - lat), 2)
        + func.pow(km_per_deg_long * (Address.longitude - long), 2)
        < less_than
    )


def store_distance_filter(lat: float, long: float) -> Exists:
    return distance_filter(Store, lat, long, func.pow(Store.delivery_range_km, 2))


def product_distance_filter(lat: float, long: float) -> Exists:
    return Product.store.has(store_distance_filter(lat, long))  # type: ignore


def service_distance_filter(lat: float, long: float) -> Exists:
    return distance_filter(Service, lat, long, Service.customer_range_km)
