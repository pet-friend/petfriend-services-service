from decimal import Decimal
from typing import Sequence

from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import Relationship, Field

from ..payments import PaymentStatusModel
from ..util import Id, TimestampModel, UUIDModel
from .stores import Store, StoreRead
from .products import Product, ProductRead


class PurchaseItemBase(UUIDModel):
    quantity: int
    unit_price: Decimal = Field(max_digits=14, decimal_places=2, ge=0)


class PurchaseItemRead(PurchaseItemBase):
    product: ProductRead


class PurchaseItem(PurchaseItemBase, table=True):
    __tablename__ = "purchase_items"
    store_id: Id
    product_id: Id
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


class PurchaseBase(PaymentStatusModel):
    buyer_id: Id
    delivery_address_id: Id


# Public database fields: id + timestamps
class PurchasePublic(PurchaseBase, UUIDModel, TimestampModel):
    pass


class PurchaseRead(PurchasePublic):
    items: Sequence[PurchaseItemRead]
    store: StoreRead


# Actual data in database table (Base + id + timestamps)
class Purchase(PurchasePublic, table=True):
    __tablename__ = "purchases"
    store_id: Id = Field(primary_key=True, foreign_key="stores.id")

    store: Store = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
    items: list[PurchaseItem] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "overlaps": "product",
        },
        back_populates="purchase",
    )

    __table_args__ = (
        PrimaryKeyConstraint("store_id", "id"),  # Make sure the order of the PK is (store_id, id)
    )
