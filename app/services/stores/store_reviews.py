from fastapi import Depends

from app.exceptions.reviews import ReviewRequirementsNotMet
from app.models.reviews import ReviewCreate
from app.models.stores import StoreReview
from app.models.payments import PaymentStatus
from app.models.util import Id
from app.repositories.reviews import StoreReviewsRepository
from .purchases import PurchasesService
from ..reviews import ReviewsService


class StoreReviewsService(ReviewsService[StoreReview, Id, Id]):
    def __init__(
        self,
        repository: StoreReviewsRepository = Depends(),
        purchases_service: PurchasesService = Depends(),
    ):
        super().__init__(repository)
        self.purchases_service = purchases_service

    async def create_review(self, data: ReviewCreate, store_id: Id, reviewer_id: Id) -> StoreReview:
        await self._check_already_exists(store_id, reviewer_id)

        purchases = await self.purchases_service.get_purchases(
            buyer_id=reviewer_id, store_id=store_id, payment_status=PaymentStatus.COMPLETED
        )
        if len(purchases) == 0:
            raise ReviewRequirementsNotMet

        return await self.repository.save(
            StoreReview(**data.model_dump(), store_id=store_id, reviewer_id=reviewer_id)
        )
