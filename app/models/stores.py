from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import field_validator

from app.models.constants.stores import (
    MIN_DELIVERY_RANGE,
    MAX_DELIVERY_RANGE,
    INVALID_DELIVERY_RANGE_MSG,
)
from .util import UUIDModel, TimestampModel


class StoreBase(SQLModel):
    name: str = Field(unique=True)
    description: Optional[str] = None
    delivery_range_km: float

    @field_validator("delivery_range_km")
    def delivery_range_verification(cls, delivery_range_km: float) -> float:
        if MIN_DELIVERY_RANGE < delivery_range_km <= MAX_DELIVERY_RANGE:
            return delivery_range_km
        raise ValueError(INVALID_DELIVERY_RANGE_MSG)


# What the Store gets from the API (Base + id)
class StoreRead(StoreBase, UUIDModel):
    # TODO: owner_id: Id (retrieved from auth credentials)
    pass


class StoreReadWithImage(StoreRead):
    image_url: str | None = None


# Actual data in database table (Base + id + timestamps)
class Store(StoreRead, TimestampModel, table=True):
    __tablename__ = "stores"


# Required attributes for creating a new record
class StoreCreate(StoreBase):
    pass
