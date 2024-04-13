from typing import Type, TypeVar, TypeVarTuple, Any

from fastapi import Depends
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stores import StoreReview, ProductReview
from app.models.services import ServiceReview
from app.models.util import Id
from app.models.reviews import ReviewRead
from app.db import get_db
from .base_repository import BaseRepository


R = TypeVar("R", bound=ReviewRead)
PK = TypeVarTuple("PK")


class ReviewsRepository(BaseRepository[R, tuple[*PK]]):
    def __init__(self, cls: Type[R], session: AsyncSession = Depends(get_db)):
        super().__init__(cls, session)

    async def count_and_average_all(self, **filters: Any) -> tuple[int, float]:
        query = (
            select(func.count(), func.avg(self.cls.rating))  # pylint: disable=not-callable
            .select_from(self.cls)
            .where(self._common_filters(**filters))
        )

        result = await self.db.exec(query)
        return result.one()


class StoreReviewsRepository(ReviewsRepository[StoreReview, Id, Id]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(StoreReview, session)


class ProductReviewsRepository(ReviewsRepository[ProductReview, Id, Id, Id]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(ProductReview, session)


class ServiceReviewsRepository(ReviewsRepository[ServiceReview, Id, Id]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(ServiceReview, session)
