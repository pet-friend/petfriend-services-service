from decimal import Decimal
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel

from .util import Id, UUIDModel, TimestampModel


class ProductBase(SQLModel):
    name: str
    description: str | None = None
    enabled: bool = True
    price: Decimal = Field(max_digits=14, decimal_places=2)
    available: int | None = None


# What the Product gets from the API (Base + id)
class ProductRead(ProductBase, UUIDModel):
    store_id: Id = Field(foreign_key="stores.id", primary_key=True)


class ProductReadWithImage(ProductRead):
    image_url: str | None = None


# Actual data in database table (Base + id + timestamps)
class Product(ProductRead, TimestampModel, table=True):
    __tablename__ = "products"

    # Two products in the same store cannot have the same name:
    __table_args__ = (
        UniqueConstraint("name", "store_id", name="product_name_uq"),
        PrimaryKeyConstraint("store_id", "id"),  # Make sure the order of the PK is (store_id, id)
    )


# Required attributes for creating a new record
class ProductCreate(ProductBase):
    pass
