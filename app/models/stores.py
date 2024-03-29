from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from pydantic import field_validator

from app.models.addresses import AddressRead, AddressCreate, Address, StoreAddressLink
from app.models.constants.stores import (
    MIN_DELIVERY_RANGE,
    MAX_DELIVERY_RANGE,
    INVALID_DELIVERY_RANGE_MSG,
    INVALID_SHIPPING_COST_MSG,
)
from .util import Id, TimestampModel, OptionalImageUrlModel, UUIDModel

if TYPE_CHECKING:
    from .products import Product


class StoreBase(SQLModel):
    name: str = Field(unique=True)
    description: str | None = None
    delivery_range_km: float
    shipping_cost: float = Field(default=0.0)

    @field_validator("delivery_range_km")
    def delivery_range_verification(cls, delivery_range_km: float) -> float:
        if MIN_DELIVERY_RANGE < delivery_range_km <= MAX_DELIVERY_RANGE:
            return delivery_range_km
        raise ValueError(INVALID_DELIVERY_RANGE_MSG)

    @field_validator("shipping_cost")
    def shipping_cost_verification(cls, shipping_cost: float) -> float:
        if shipping_cost >= 0:
            return shipping_cost
        raise ValueError(INVALID_SHIPPING_COST_MSG)


# Public database fields
class StorePublic(UUIDModel, StoreBase):
    owner_id: Id


# What the user gets from the API (Public + image)
class StoreRead(StorePublic, OptionalImageUrlModel):
    address: AddressRead | None


# Actual data in database table (Base + id + timestamps)
class Store(StorePublic, TimestampModel, table=True):
    __tablename__ = "stores"

    address: Address | None = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete", "uselist": False},
        link_model=StoreAddressLink,
    )
    products: list["Product"] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
        back_populates="store",
    )


# Required attributes for creating a new record
class StoreCreate(StoreBase):
    address: AddressCreate | None = None
