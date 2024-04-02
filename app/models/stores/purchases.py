from decimal import Decimal
from enum import StrEnum
from typing import Literal, Sequence

from pydantic import BaseModel
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import Relationship, Field, SQLModel

from ..util import Id, TimestampModel, UUIDModel
from .stores import Store
from .products import Product


class PurchaseItemBase(UUIDModel):
    product_id: Id
    quantity: int
    unit_price: Decimal = Field(max_digits=14, decimal_places=2, ge=0)


class PurchaseItem(PurchaseItemBase, table=True):
    __tablename__ = "purchase_items"
    store_id: Id
    purchase_id: Id

    purchase: "Purchase" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
        back_populates="items",
    )
    product: Product = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "overlaps": "purchase"}
    )

    __table_args__ = (
        ForeignKeyConstraint(["store_id", "product_id"], ["products.store_id", "products.id"]),
        ForeignKeyConstraint(["store_id", "purchase_id"], ["purchases.store_id", "purchases.id"]),
    )


class PurchaseStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


PurchaseStatusUpdate = Literal[
    PurchaseStatus.IN_PROGRESS, PurchaseStatus.COMPLETED, PurchaseStatus.CANCELLED
]


class PurchaseUpdate(BaseModel):
    status: PurchaseStatusUpdate


class PurchaseBase(SQLModel):
    store_id: Id = Field(primary_key=True, foreign_key="stores.id")
    status: PurchaseStatus
    payment_url: str | None = None
    buyer_id: Id
    delivery_address_id: Id


# Public database fields: id + timestamps
class PurchasePublic(PurchaseBase, UUIDModel, TimestampModel):
    pass


class PurchaseRead(PurchasePublic):
    items: Sequence[PurchaseItemBase]


# Actual data in database table (Base + id + timestamps)
class Purchase(PurchasePublic, table=True):
    __tablename__ = "purchases"

    store: Store = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
    items: list[PurchaseItem] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "overlaps": "product",
        },
        back_populates="purchase",
    )

    # Two products in the same store cannot have the same name:
    __table_args__ = (
        PrimaryKeyConstraint("store_id", "id"),  # Make sure the order of the PK is (store_id, id)
    )
