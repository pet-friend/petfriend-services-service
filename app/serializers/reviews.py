from typing import Sequence, TypeVar, Generic

from pydantic import BaseModel

from app.models.reviews import ReviewRead

R = TypeVar("R", bound=ReviewRead)


class ReviewList(BaseModel, Generic[R]):
    reviews: Sequence[R]
    amount: int
    average_rating: float | None
