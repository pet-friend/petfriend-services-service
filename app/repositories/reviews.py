from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stores import StoreReview, ProductReview
from app.models.services import ServiceReview
from app.models.util import Id
from app.db import get_db
from .base_repository import BaseRepository


class StoreReviewsRepository(BaseRepository[StoreReview, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(StoreReview, session)


class ProductReviewsRepository(BaseRepository[ProductReview, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(ProductReview, session)


class ServiceReviewsRepository(BaseRepository[ServiceReview, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(ServiceReview, session)
