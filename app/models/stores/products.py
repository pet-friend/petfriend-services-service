from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import field_validator, model_validator
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from ..review import Review, ReviewsScoreAverage, set_review_score_average_column
from ..util import Id, UUIDModel, TimestampModel, OptionalImageUrlModel
from .stores import Store

MAX_CATEGORIES_PER_PRODUCT = 3


class Category(StrEnum):
    ALIMENTOS = "alimentos"
    JUGUETES = "juguetes"
    HIGIENE_Y_CUIDADO = "higiene_y_cuidado"
    VIAJES = "viajes"
    ACCESORIOS = "accesorios"
    SALUD_Y_BIENESTAR = "salud_y_bienestar"
    CORREAS_Y_COLLARES = "correas_y_collares"
    CUCHAS = "cuchas"
    CAMAS = "camas"
    PLATOS_Y_COMEDEROS = "platos_y_comederos"


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
    price: Decimal = Field(max_digits=14, decimal_places=2, gt=0)
    percent_off: Decimal = Field(max_digits=5, decimal_places=2, ge=0, le=100, default=0)
    available: int | None = Field(None, ge=0)


# What the Product gets from the API (Base + id)
class ProductPublic(ProductBase, ReviewsScoreAverage, UUIDModel):
    store_id: Id = Field(foreign_key="stores.id", primary_key=True)


class ProductRead(ProductPublic, OptionalImageUrlModel):
    categories: list[Category]

    @model_validator(mode="before")
    @classmethod
    def check_categories_format(cls, data: Any) -> Any:
        if isinstance(data, Product):
            new_data = data.model_dump()
            new_data["categories"] = [c.category for c in data._categories]
            return new_data

        return data


# Actual data in database table (Base + id + timestamps)
class Product(ProductPublic, TimestampModel, table=True):
    __tablename__ = "products"

    _categories: list[ProductCategories] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        }
    )

    store: "Store" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}, back_populates="products"
    )
    # Not populated, only used for deleting reviews when a product is deleted
    _reviews: list["ProductReview"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Two products in the same store cannot have the same name:
    __table_args__ = (
        UniqueConstraint("name", "store_id", name="product_name_uq"),
        PrimaryKeyConstraint("store_id", "id"),  # Make sure the order of the PK is (store_id, id)
    )


# Required attributes for creating a new record
class ProductCreate(ProductBase):
    categories: list[Category]

    @field_validator("categories")
    def validate_categories(cls, v: list[Category]) -> list[Category]:
        if len(v) > MAX_CATEGORIES_PER_PRODUCT:
            raise ValueError(
                f"Cannot have more than {MAX_CATEGORIES_PER_PRODUCT} categories per product"
            )
        return v


class ProductReview(Review, table=True):
    __tablename__ = "product_reviews"

    store_id: Id
    product_id: Id

    __table_args__ = (
        ForeignKeyConstraint(["store_id", "product_id"], ["products.store_id", "products.id"]),
    )


set_review_score_average_column(
    Product,
    ProductReview,
    (ProductReview.store_id == Product.store_id) & (ProductReview.product_id == Product.id),
)
