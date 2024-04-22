from typing import Generic, Any, Literal, Sequence, Unpack

from app.exceptions.repository import RecordNotFound
from app.exceptions.reviews import AlreadyReviewed, ReviewNotFound
from app.models.reviews import ReviewCreate
from app.models.util import SortOrder
from app.repositories.reviews import ReviewsRepository, R, PK

ReviewSortBy = Literal["updated_at", "created_at", "rating"]


class ReviewsService(Generic[R, *PK]):
    repository: ReviewsRepository[R, *PK]

    def __init__(self, repository: ReviewsRepository[R, *PK]):
        self.repository = repository

    async def get_review_by_id(self, *review_pk: Unpack[PK]) -> R:
        review = await self.repository.get_by_id(review_pk)
        if review is None:
            raise ReviewNotFound
        return review

    async def update_review(self, data: ReviewCreate, *review_pk: Unpack[PK]) -> R:
        try:
            return await self.repository.update(review_pk, data.model_dump())
        except RecordNotFound as e:
            raise ReviewNotFound from e

    async def delete_review(self, *review_pk: Unpack[PK]) -> None:
        try:
            await self.repository.delete(review_pk)
        except RecordNotFound as e:
            raise ReviewNotFound from e

    async def get_reviews(
        self,
        limit: int,
        skip: int,
        sort_by: ReviewSortBy | None = None,
        sort_order: SortOrder = SortOrder.DESCENDING,
        **filters: Any,
    ) -> Sequence[R]:
        return await self.repository.get_all(skip, limit, sort_by, sort_order, **filters)

    async def count_and_average_reviews(self, **filters: Any) -> tuple[int, float | None]:
        return await self.repository.count_and_average_all(**filters)

    async def _check_already_exists(self, *review_pk: Unpack[PK]) -> None:
        if await self.repository.get_by_id(review_pk) is not None:
            raise AlreadyReviewed
