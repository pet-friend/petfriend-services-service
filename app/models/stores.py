from typing import Optional
from uuid import uuid4
from sqlmodel import Field, SQLModel
from pydantic import UUID4, field_validator

from app.models.constants.stores import (
    MIN_DELIVERY_RANGE,
    MAX_DELIVERY_RANGE,
    INVALID_DELIVERY_RANGE_MSG,
)
from .util import Id, UUIDModel, TimestampModel


class Image(SQLModel):
    name: str
    data: bytes


class StoreBase(SQLModel):
    name: str = Field(unique=True)
    description: Optional[str] = None
    # image: con lo de azure
    address: Id = Field(default_factory=uuid4)
    delivery_range_km: float

    @field_validator("delivery_range_km")
    def delivery_range_verification(cls, delivery_range_km: float) -> float:
        if delivery_range_km > MIN_DELIVERY_RANGE and delivery_range_km <= MAX_DELIVERY_RANGE:
            return delivery_range_km
        raise ValueError(INVALID_DELIVERY_RANGE_MSG)


# What the user gets from the API (Base + id)
class StoreRead(StoreBase, UUIDModel):
    # TODO: owner_id: Id (retrieved from auth credentials)
    pass


# Actual data in database table (Base + id + timestamps)
class Store(StoreRead, TimestampModel, table=True):
    __tablename__ = "stores"


# Required attributes for creating a new record
class StoreCreate(StoreBase):
    pass
