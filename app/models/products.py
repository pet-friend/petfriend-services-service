from decimal import Decimal
from enum import StrEnum
from typing import List
from pydantic import field_validator
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.orm import Mapped
from .util import Id, UUIDModel, TimestampModel, OptionalImageUrlModel

# Define enum for categories dynamically using the constant
# CategoryEnum = Enum("CategoryEnum", ALLOWED_PRODUCT_CATEGORIES)
MAX_CATEGORIES_PER_PRODUCT = 3


class Category(StrEnum):
    Alimentos = "alimentos"
    Juguetes = "juguetes"
    Higiene_y_Cuidado = "higiene y cuidado"
    Viajes = "viajes"
    Accesorios = "accesorios"
    Salud_y_Bienestar = "salud y bienestar"
    Correas_y_Collares = "correas y collares"
    Cuchas = "cuchas"
    Camas = "camas"
    Platos_y_Comederos = "platos y comederos"


# class Category(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True, autoincrement=True)
#     name: str = Field(max_length=100, unique=True)


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
    # TODO: add min_items=1 and max_items=MAX_CATEGORIES_PER_PRODUCT

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
