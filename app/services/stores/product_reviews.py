from fastapi import Depends

from app.exceptions.reviews import ReviewRequirementsNotMet
from app.models.reviews import ReviewCreate
from app.models.stores import ProductReview, Purchase
from app.models.payments import PaymentStatus
from app.models.util import Id
from app.repositories.reviews import ProductReviewsRepository
from .purchases import PurchasesService
from ..reviews import ReviewsService


class ProductReviewsService(ReviewsService[ProductReview, Id, Id, Id]):
    def __init__(
        self,
        repository: ProductReviewsRepository = Depends(),
        purchases_service: PurchasesService = Depends(),
    ):
        super().__init__(repository)
        self.purchases_service = purchases_service

    async def create_review(
        self, data: ReviewCreate, store_id: Id, product_id: Id, reviewer_id: Id
    ) -> ProductReview:
        await self._check_already_exists(store_id, product_id, reviewer_id)

        purchases = await self.purchases_service.get_purchases(
            buyer_id=reviewer_id, store_id=store_id, payment_status=PaymentStatus.COMPLETED
        )
        if not any(self.__product_purchased(p, product_id) for p in purchases):
            raise ReviewRequirementsNotMet

        return await self.repository.save(
            ProductReview(
                **data.model_dump(),
                store_id=store_id,
                product_id=product_id,
                reviewer_id=reviewer_id
            )
        )

    def __product_purchased(self, purchase: Purchase, product_id: Id) -> bool:
        return any(i.product_id == product_id for i in purchase.items)
