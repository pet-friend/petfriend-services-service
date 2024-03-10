from math import pi, radians, cos

from sqlmodel import func
from sqlalchemy import Exists

from ..models.stores import Store
from ..models.addresses import Address

EARTH_RADIUS_KM = 6371.009
KM_PER_DEG_LAT = 2 * pi * EARTH_RADIUS_KM / 360.0


def store_distance_filter(lat: float, long: float) -> Exists:
    """
    Based on https://stackoverflow.com/a/5207131
    Should be decently accurate for small distances (a few km)
    """

    km_per_deg_long = KM_PER_DEG_LAT * cos(radians(lat))
    return Store.address.has(  # type: ignore
        func.pow(KM_PER_DEG_LAT * (Address.latitude - lat), 2)
        + func.pow(km_per_deg_long * (Address.longitude - long), 2)
        < func.pow(Store.delivery_range_km, 2)
    )
