from decimal import Decimal
from enum import Enum
from typing import List
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.orm import Mapped
from app.models.constants.categories import (
    ALLOWED_PRODUCT_CATEGORIES,
    MAX_CATEGORIES_PER_PRODUCT,
)
from .util import Id, UUIDModel, TimestampModel, OptionalImageUrlModel

# Define enum for categories dynamically using the constant
CategoryEnum = Enum("CategoryEnum", ALLOWED_PRODUCT_CATEGORIES)


# class Category(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True, autoincrement=True)
#     name: str = Field(max_length=100, unique=True)


class ProductCategoriesLink(SQLModel, table=True):
    __tablename__ = "product_categories_link"

    product_id: Id | None = Field(default=None, primary_key=True)
    category: CategoryEnum | None = Field(default=None, primary_key=True)
    store_id: Id | None = Field(default=None, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(["store_id", "product_id"], ["products.store_id", "products.id"]),
    )


class ProductBase(SQLModel):

    name: str
    description: str | None = None
    enabled: bool = True
    price: Decimal = Field(max_digits=14, decimal_places=2, ge=0)
    available: int | None = None


# What the Product gets from the API (Base + id)
class ProductRead(ProductBase, UUIDModel):
    store_id: Id = Field(foreign_key="stores.id", primary_key=True)


class ProductReadWithImage(ProductRead, OptionalImageUrlModel):
    pass


# Actual data in database table (Base + id + timestamps)
class Product(ProductRead, TimestampModel, table=True):
    __tablename__ = "products"

    categories: List[CategoryEnum] = Relationship(
        link_model=ProductCategoriesLink,
        back_populates="products",
    )
    # TODO: add min_items=1 and max_items=MAX_CATEGORIES_PER_PRODUCT

    # Two products in the same store cannot have the same name:
    __table_args__ = (
        UniqueConstraint("name", "store_id", name="product_name_uq"),
        PrimaryKeyConstraint("store_id", "id"),  # Make sure the order of the PK is (store_id, id)
    )


# Required attributes for creating a new record
class ProductCreate(ProductBase):
    # categories: List[CategoryEnum]
    pass
