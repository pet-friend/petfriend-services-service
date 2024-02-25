from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from pydantic import field_validator

from app.models.constants.stores import (
    MIN_DELIVERY_RANGE,
    MAX_DELIVERY_RANGE,
    INVALID_DELIVERY_RANGE_MSG,
)
from .util import Id, TimestampModel, OptionalImageUrlModel
from .service import Service

if TYPE_CHECKING:
    from .products import Product


class StoreBase(SQLModel):
    name: str = Field(unique=True)
    description: str | None = None
    delivery_range_km: float

    @field_validator("delivery_range_km")
    def delivery_range_verification(cls, delivery_range_km: float) -> float:
        if MIN_DELIVERY_RANGE < delivery_range_km <= MAX_DELIVERY_RANGE:
            return delivery_range_km
        raise ValueError(INVALID_DELIVERY_RANGE_MSG)


# What the Store gets from the API (Base + id)
class StoreRead(StoreBase):
    id: Id = Field(foreign_key="services.id", primary_key=True)


class StoreReadWithImage(StoreRead, OptionalImageUrlModel):
    pass


# Actual data in database table (Base + id + timestamps)
class Store(StoreRead, TimestampModel, table=True):
    __tablename__ = "stores"

    owner_id: Id
    service: Service = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}, back_populates="store"
    )
    products: list["Product"] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )


# Required attributes for creating a new record
class StoreCreate(StoreBase):
    pass
