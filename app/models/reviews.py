from typing import Type, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import column_property

from .util import Id, TimestampModel


class ReviewBase(SQLModel):
    rating: int = Field(ge=1, le=5)
    comment: str


class ReviewRead(ReviewBase, TimestampModel):
    reviewer_id: Id = Field(primary_key=True)


# Tables are defined in ./stores/stores.py, ./stores/products.py, and ./services/services.py
# for each of their reviews


class ReviewCreate(ReviewBase):
    pass


class ReviewsRatingAverage(SQLModel):
    reviews_average_rating: float | None = None


def set_review_rating_average_column(
    cls: Type[ReviewsRatingAverage], review_cls: Type[ReviewRead], join_condition: Any
) -> Any:
    """
    Adds a SQLAlchemy
    [`column_property`](https://docs.sqlalchemy.org/en/13/orm/mapped_sql_expr.html#using-column-property)
    to the class `cls` that calculates the average rating of the reviews that are related to
    the class `cls` through the `join_condition`.

    This allows the average rating to be queried along with the other columns of the class `cls`.
    """
    query = select(func.avg(review_cls.rating)).where(join_condition).correlate_except(review_cls)
    column = column_property(query.scalar_subquery())
    cls.reviews_average_rating = column  # type: ignore

    # Hack to remove the column from the table definition:
    # Unfortunately SQLModel does not 100% support SQLAlchemy's column_property yet so if we
    # don't remove it then alembic will try it as a new column in the database table
    cols = cls.metadata.tables[cls.__tablename__]._columns  # type: ignore
    cols.remove(cols["reviews_average_rating"])
