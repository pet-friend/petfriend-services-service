from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from pydantic import field_validator

from ..addresses import AddressRead, AddressCreate, Address, StoreAddressLink
from ..constants.stores import (
    MIN_DELIVERY_RANGE,
    MAX_DELIVERY_RANGE,
    INVALID_DELIVERY_RANGE_MSG,
    INVALID_SHIPPING_COST_MSG,
)
from ..review import Review, ReviewsScoreAverage, set_review_score_average_column
from ..util import Id, TimestampModel, OptionalImageUrlModel, UUIDModel

if TYPE_CHECKING:
    from .products import Product


class StoreBase(SQLModel):
    name: str = Field(unique=True)
    description: str | None = None
    delivery_range_km: float
    shipping_cost: Decimal = Field(max_digits=14, decimal_places=2, default=Decimal(0))

    @field_validator("delivery_range_km")
    def delivery_range_verification(cls, delivery_range_km: float) -> float:
        if MIN_DELIVERY_RANGE < delivery_range_km <= MAX_DELIVERY_RANGE:
            return delivery_range_km
        raise ValueError(INVALID_DELIVERY_RANGE_MSG)

    @field_validator("shipping_cost")
    def shipping_cost_verification(cls, shipping_cost: Decimal) -> Decimal:
        if shipping_cost >= 0:
            return shipping_cost
        raise ValueError(INVALID_SHIPPING_COST_MSG)


# Public database fields
class StorePublic(UUIDModel, StoreBase, ReviewsScoreAverage):
    owner_id: Id


# What the user gets from the API (Public + image + address)
class StoreRead(StorePublic, OptionalImageUrlModel):
    address: AddressRead


# Actual data in database table (Base + id + timestamps)
class Store(StorePublic, TimestampModel, table=True):
    __tablename__ = "stores"

    address: Address = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "single_parent": True,
        },
        link_model=StoreAddressLink,
    )
    products: list["Product"] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
        back_populates="store",
    )
    # Not populated, only used for deleting reviews when a store is deleted
    _reviews: list["StoreReview"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def range_km(self) -> float:
        return self.delivery_range_km


# Required attributes for creating a new record
class StoreCreate(StoreBase):
    address: AddressCreate


class StoreReview(Review, table=True):
    __tablename__ = "store_reviews"

    store_id: Id = Field(foreign_key="stores.id")


set_review_score_average_column(Store, StoreReview, StoreReview.store_id == Store.id)
