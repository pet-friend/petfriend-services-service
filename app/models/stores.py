from typing import Optional
from sqlmodel import SQLModel
from pydantic import UUID4, validator
from .util import Id, UUIDModel, TimestampModel


class Image(SQLModel):
    name: str
    data: bytes


class StoreBase(SQLModel):
    name: str
    description: Optional[str] = None
    # image: con lo de azure
    address: Id = UUID4()
    delivery_range_km: float

    @validator("delivery_range_km")
    def delivery_range_verification(cls, delivery_range_km: float) -> float:
        if delivery_range_km > 0 and delivery_range_km <= 20:
            return delivery_range_km
        raise ValueError("invalid delivery range")


# What the user gets from the API (Base + id)
class StoreRead(StoreBase, UUIDModel):
    # owner_id: Id
    pass


# Actual data in database table (Base + id + timestamps)
class Store(StoreRead, TimestampModel, table=True):
    __tablename__ = "stores"


# Required attributes for creating a new record
class StoreCreate(StoreBase):
    pass
