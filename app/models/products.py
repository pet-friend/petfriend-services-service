from decimal import Decimal
from enum import StrEnum
from typing import List
from pydantic import field_validator
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from .util import Id, UUIDModel, TimestampModel, OptionalImageUrlModel

MAX_CATEGORIES_PER_PRODUCT = 3


class Category(StrEnum):
    ALIMENTOS = "alimentos"
    JUGUETES = "juguetes"
    HIGIENE_Y_CUIDADO = "higiene y cuidado"
    VIAJES = "viajes"
    ACCESORIOS = "accesorios"
    SALUD_Y_BIENESTAR = "salud y bienestar"
    CORREAS_Y_COLLARES = "correas y collares"
    CUCHAS = "cuchas"
    CAMAS = "camas"
    PLATOS_Y_COMEDEROS = "platos y comederos"


class ProductCategories(SQLModel, table=True):
    __tablename__ = "product_categories"

    store_id: Id = Field(primary_key=True)
    product_id: Id = Field(primary_key=True)
    category: Category = Field(primary_key=True)

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
class ProductPublic(ProductBase, UUIDModel):
    store_id: Id = Field(foreign_key="stores.id", primary_key=True)


class ProductRead(ProductPublic, OptionalImageUrlModel):
    categories: List[Category]


# Actual data in database table (Base + id + timestamps)
class Product(ProductPublic, TimestampModel, table=True):
    __tablename__ = "products"

    _categories: list[ProductCategories] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        }
    )

    # Two products in the same store cannot have the same name:
    __table_args__ = (
        UniqueConstraint("name", "store_id", name="product_name_uq"),
        PrimaryKeyConstraint("store_id", "id"),  # Make sure the order of the PK is (store_id, id)
    )


# Required attributes for creating a new record
class ProductCreate(ProductBase):
    categories: List[Category]

    @field_validator("categories")
    def validate_categories(cls, v: List[Category]) -> List[Category]:
        if len(v) > MAX_CATEGORIES_PER_PRODUCT:
            raise ValueError(
                f"Cannot have more than {MAX_CATEGORIES_PER_PRODUCT} categories per product"
            )
        return v
