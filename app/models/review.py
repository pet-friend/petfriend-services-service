from typing import Type, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import column_property

from .util import UUIDModel


class ReviewBase(SQLModel):
    score: int = Field(ge=1, le=5)
    comment: str


class ReviewRead(ReviewBase):
    pass


# Tables are defined in ./stores/stores.py, ./stores/products.py, and ./services/services.py
# for each of their reviews
class Review(ReviewRead, UUIDModel):
    pass


class ReviewCreate(ReviewBase):
    pass


class ReviewsScoreAverage(SQLModel):
    reviews_score_average: float | None


def set_review_score_average_column(
    cls: Type[ReviewsScoreAverage], review_cls: Type[Review], join_condition: Any
) -> Any:
    """
    Adds a SQLAlchemy
    [`column_property`](https://docs.sqlalchemy.org/en/13/orm/mapped_sql_expr.html#using-column-property)
    to the class `cls` that calculates the average score of the reviews that are related to
    the class `cls` through the `join_condition`.

    This allows the average score to be queried along with the other columns of the class `cls`.
    """
    query = select(func.avg(review_cls.score)).where(join_condition).correlate_except(review_cls)
    cls.reviews_score_average = column_property(query)  # type: ignore

    # Hack to remove the column from the table definition:
    # Unfortunately SQLModel does not 100% support SQLAlchemy's column_property yet so if we
    # don't remove it then alembic will try it as a new column in the database table
    cols = cls.metadata.tables[cls.__tablename__]._columns  # type: ignore
    cols.remove(cols["reviews_score_average"])
