from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.exceptions.repository import RecordNotFound
from app.exceptions.reviews import ReviewNotFound, ReviewRequirementsNotMet, AlreadyReviewed
from app.models.payments import PaymentStatus
from app.models.stores import Purchase, PurchaseItem
from app.models.services import ServiceReview, Appointment
from app.models.stores import StoreReview, ProductReview
from app.models.util import SortOrder
from app.repositories.reviews import (
    ServiceReviewsRepository,
    StoreReviewsRepository,
    ProductReviewsRepository,
)
from app.services.services import AppointmentsService, ServiceReviewsService
from app.services.stores import StoreReviewsService, ProductReviewsService
from app.services.stores.purchases import PurchasesService
from tests.factories.review_factories import ReviewCreateFactory
from tests.util import CustomMatcher


class TestReviewsServices:
    def setup_method(self) -> None:
        self.review_create = ReviewCreateFactory().build()
        self.repository = AsyncMock(spec=ServiceReviewsRepository)
        self.service = ServiceReviewsService(self.repository, AsyncMock(spec=AppointmentsService))
        self.review = ServiceReview(
            **self.review_create.model_dump(), reviewer_id=uuid4(), service_id=uuid4()
        )

    async def test_create_service_review_should_call_repository_save(self) -> None:
        # Given
        appointments_service = AsyncMock(spec=AppointmentsService)
        service = ServiceReviewsService(self.repository, appointments_service)
        now = datetime.now(timezone.utc)

        appointment = Appointment(
            service_id=self.review.service_id,
            customer_id=self.review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            start=now - timedelta(hours=24),
            end=now - timedelta(hours=20),
            customer_address_id=uuid4(),
        )
        appointments_service.get_appointments.return_value = [appointment]
        self.repository.get_by_id.return_value = None
        self.repository.save = AsyncMock(return_value=self.review)

        # When
        saved_record = await service.create_review(
            self.review_create,
            reviewer_id=self.review.reviewer_id,
            service_id=self.review.service_id,
            now=now,
        )

        # Then
        excluded = {"id", "updated_at", "created_at"}
        assert saved_record.model_dump(exclude=excluded) == self.review.model_dump(exclude=excluded)
        self.repository.get_by_id.assert_called_once_with(
            (saved_record.service_id, saved_record.reviewer_id)
        )
        self.repository.save.assert_called_once_with(
            CustomMatcher[ServiceReview](
                lambda r: r.model_dump().items() >= self.review_create.model_dump().items()
            )
        )
        appointments_service.get_appointments.assert_called_once_with(
            before=now,
            include_partial=True,
            customer_id=self.review.reviewer_id,
            service_id=self.review.service_id,
            payment_status=PaymentStatus.COMPLETED,
        )

    async def test_create_service_review_fails_if_already_reviewed(self) -> None:
        # Given
        appointments_service = AsyncMock(spec=AppointmentsService)
        service = ServiceReviewsService(self.repository, appointments_service)
        now = datetime.now(timezone.utc)

        appointment = Appointment(
            service_id=self.review.service_id,
            customer_id=self.review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            start=now - timedelta(hours=24),
            end=now - timedelta(hours=20),
            customer_address_id=uuid4(),
        )
        appointments_service.get_appointments.return_value = [appointment]
        self.repository.get_by_id.return_value = self.review
        self.repository.save = AsyncMock(return_value=self.review)

        # When, Then
        with pytest.raises(AlreadyReviewed):
            await service.create_review(
                self.review_create,
                reviewer_id=self.review.reviewer_id,
                service_id=self.review.service_id,
                now=now,
            )

        # Then
        self.repository.save.assert_not_called()

    async def test_create_service_review_fails_if_no_matching_appointments(self) -> None:
        # Given
        appointments_service = AsyncMock(spec=AppointmentsService)
        service = ServiceReviewsService(self.repository, appointments_service)
        now = datetime.now(timezone.utc)

        appointments_service.get_appointments.return_value = []
        self.repository.get_by_id.return_value = None
        self.repository.save = AsyncMock(return_value=self.review)

        # When, Then
        with pytest.raises(ReviewRequirementsNotMet):
            await service.create_review(
                self.review_create,
                reviewer_id=self.review.reviewer_id,
                service_id=self.review.service_id,
                now=now,
            )

        # Then
        self.repository.save.assert_not_called()

    async def test_create_store_review_should_call_repository_save(self) -> None:
        # Given
        purchases_service = AsyncMock(spec=PurchasesService)
        repository = AsyncMock(spec=StoreReviewsRepository)
        service = StoreReviewsService(repository, purchases_service)

        review = StoreReview(
            **self.review_create.model_dump(), reviewer_id=uuid4(), store_id=uuid4()
        )
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store_id=review.store_id,
            items=items,
            buyer_id=review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            delivery_address_id=uuid4(),
        )
        purchases_service.get_purchases.return_value = [purchase]
        repository.get_by_id.return_value = None
        repository.save = AsyncMock(return_value=review)

        # When
        saved_record = await service.create_review(
            self.review_create,
            reviewer_id=review.reviewer_id,
            store_id=review.store_id,
        )

        # Then
        excluded = {"id", "updated_at", "created_at"}
        assert saved_record.model_dump(exclude=excluded) == review.model_dump(exclude=excluded)
        repository.get_by_id.assert_called_once_with((review.store_id, review.reviewer_id))
        repository.save.assert_called_once_with(
            CustomMatcher[StoreReview](
                lambda r: r.model_dump().items() >= self.review_create.model_dump().items()
            )
        )
        purchases_service.get_purchases.assert_called_once_with(
            buyer_id=review.reviewer_id,
            store_id=review.store_id,
            payment_status=PaymentStatus.COMPLETED,
        )

    async def test_create_store_review_fails_if_already_reviewed(self) -> None:
        # Given
        purchases_service = AsyncMock(spec=PurchasesService)
        repository = AsyncMock(spec=StoreReviewsRepository)
        service = StoreReviewsService(repository, purchases_service)

        review = StoreReview(
            **self.review_create.model_dump(), reviewer_id=uuid4(), store_id=uuid4()
        )
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store_id=review.store_id,
            items=items,
            buyer_id=review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            delivery_address_id=uuid4(),
        )
        purchases_service.get_purchases.return_value = [purchase]
        repository.get_by_id.return_value = review
        repository.save = AsyncMock(return_value=review)

        # When, Then
        with pytest.raises(AlreadyReviewed):
            await service.create_review(
                self.review_create,
                reviewer_id=review.reviewer_id,
                store_id=review.store_id,
            )

        # Then
        repository.save.assert_not_called()

    async def test_create_store_review_fails_if_no_matching_purchases(self) -> None:
        # Given
        purchases_service = AsyncMock(spec=PurchasesService)
        repository = AsyncMock(spec=StoreReviewsRepository)
        service = StoreReviewsService(repository, purchases_service)

        review = StoreReview(
            **self.review_create.model_dump(), reviewer_id=uuid4(), store_id=uuid4()
        )
        purchases_service.get_purchases.return_value = []
        repository.get_by_id.return_value = None
        repository.save = AsyncMock(return_value=review)

        # When, Then
        with pytest.raises(ReviewRequirementsNotMet):
            await service.create_review(
                self.review_create,
                reviewer_id=review.reviewer_id,
                store_id=review.store_id,
            )

        # Then
        repository.save.assert_not_called()
        purchases_service.get_purchases.assert_called_once_with(
            buyer_id=review.reviewer_id,
            store_id=review.store_id,
            payment_status=PaymentStatus.COMPLETED,
        )

    async def test_create_product_review_should_call_repository_save(self) -> None:
        # Given
        purchases_service = AsyncMock(spec=PurchasesService)
        repository = AsyncMock(spec=ProductReviewsRepository)
        service = ProductReviewsService(repository, purchases_service)

        review = ProductReview(
            **self.review_create.model_dump(),
            reviewer_id=uuid4(),
            store_id=uuid4(),
            product_id=uuid4(),
        )
        items = [
            PurchaseItem(product_id=review.product_id, quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store_id=review.store_id,
            items=items,
            buyer_id=review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            delivery_address_id=uuid4(),
        )
        purchases_service.get_purchases.return_value = [purchase]
        repository.get_by_id.return_value = None
        repository.save = AsyncMock(return_value=review)

        # When
        saved_record = await service.create_review(
            self.review_create,
            reviewer_id=review.reviewer_id,
            store_id=review.store_id,
            product_id=review.product_id,
        )

        # Then
        excluded = {"id", "updated_at", "created_at"}
        assert saved_record.model_dump(exclude=excluded) == review.model_dump(exclude=excluded)
        repository.get_by_id.assert_called_once_with(
            (review.store_id, review.product_id, review.reviewer_id)
        )
        repository.save.assert_called_once_with(
            CustomMatcher[ProductReview](
                lambda r: r.model_dump().items() >= self.review_create.model_dump().items()
            )
        )
        purchases_service.get_purchases.assert_called_once_with(
            buyer_id=review.reviewer_id,
            store_id=review.store_id,
            payment_status=PaymentStatus.COMPLETED,
        )

    async def test_create_product_review_fails_if_already_reviewed(self) -> None:
        # Given
        purchases_service = AsyncMock(spec=PurchasesService)
        repository = AsyncMock(spec=ProductReviewsRepository)
        service = ProductReviewsService(repository, purchases_service)

        review = ProductReview(
            **self.review_create.model_dump(),
            reviewer_id=uuid4(),
            store_id=uuid4(),
            product_id=uuid4(),
        )
        items = [
            PurchaseItem(product_id=review.product_id, quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store_id=review.store_id,
            items=items,
            buyer_id=review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            delivery_address_id=uuid4(),
        )
        purchases_service.get_purchases.return_value = [purchase]
        repository.get_by_id.return_value = review
        repository.save = AsyncMock(return_value=review)

        # When, Then
        with pytest.raises(AlreadyReviewed):
            await service.create_review(
                self.review_create,
                reviewer_id=review.reviewer_id,
                store_id=review.store_id,
                product_id=review.product_id,
            )

        # Then
        repository.save.assert_not_called()

    async def test_create_product_review_fails_if_no_matching_purchases(self) -> None:
        # Given
        purchases_service = AsyncMock(spec=PurchasesService)
        repository = AsyncMock(spec=ProductReviewsRepository)
        service = ProductReviewsService(repository, purchases_service)

        review = ProductReview(
            **self.review_create.model_dump(),
            reviewer_id=uuid4(),
            store_id=uuid4(),
            product_id=uuid4(),
        )
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store_id=review.store_id,
            items=items,
            buyer_id=review.reviewer_id,
            payment_status=PaymentStatus.COMPLETED,
            delivery_address_id=uuid4(),
        )
        purchases_service.get_purchases.return_value = [purchase]
        repository.get_by_id.return_value = None
        repository.save = AsyncMock(return_value=review)

        # When, Then
        with pytest.raises(ReviewRequirementsNotMet):
            await service.create_review(
                self.review_create,
                reviewer_id=review.reviewer_id,
                store_id=review.store_id,
                product_id=review.product_id,
            )

        # Then
        repository.save.assert_not_called()
        purchases_service.get_purchases.assert_called_once_with(
            buyer_id=review.reviewer_id,
            store_id=review.store_id,
            payment_status=PaymentStatus.COMPLETED,
        )

    async def test_get_reviews_should_call_repository_get_all(self) -> None:
        # Given
        self.repository.get_all = AsyncMock(return_value=[self.review])

        # When
        fetched_record = await self.service.get_reviews(
            1, 1, sort_by="created_at", sort_order=SortOrder.DESCENDING, filter_name="filter_value"
        )

        # Then
        assert fetched_record == [self.review]
        self.repository.get_all.assert_called_once_with(
            1, 1, "created_at", SortOrder.DESCENDING, filter_name="filter_value"
        )

    async def test_count_and_average_reviews_should_call_repository_count_all(self) -> None:
        # Given
        self.repository.count_and_average_all = AsyncMock(return_value=(1, 2))

        # When
        fetched_record = await self.service.count_and_average_reviews(filter_name="filter_value")

        # Then
        assert fetched_record == (1, 2)
        self.repository.count_and_average_all.assert_called_once_with(filter_name="filter_value")

    async def test_get_review_by_id_should_call_repository_get_by_id(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.review)

        # When
        fetched_record = await self.service.get_review_by_id(
            self.review.service_id, self.review.reviewer_id
        )

        # Then
        assert fetched_record == self.review
        self.repository.get_by_id.assert_called_once_with(
            (self.review.service_id, self.review.reviewer_id)
        )

    async def test_update_review_should_call_repository_update(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.review)
        self.repository.update = AsyncMock(return_value=self.review)

        # When
        fetched_record = await self.service.update_review(
            self.review_create,
            self.review.service_id,
            self.review.reviewer_id,
        )

        # Then
        assert fetched_record == self.review
        self.repository.update.assert_called_once_with(
            (self.review.service_id, self.review.reviewer_id), self.review_create.model_dump()
        )

    async def test_update_inexistent_review_should_raise_review_not_found(self) -> None:
        # Given
        self.repository.update = AsyncMock(side_effect=RecordNotFound)

        # When, Then
        review_pk = (uuid4(), uuid4())
        with pytest.raises(ReviewNotFound):
            await self.service.update_review(
                self.review_create,
                *review_pk,
            )

    async def test_delete_review_should_call_repository_delete(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.review)
        self.repository.delete = AsyncMock(return_value=None)

        # When
        await self.service.delete_review(self.review.service_id, self.review.reviewer_id)

        # Then
        self.repository.delete.assert_called_once_with(
            (self.review.service_id, self.review.reviewer_id)
        )

    async def test_delete_inexistent_review_should_raise_review_not_found(self) -> None:
        # Given
        self.repository.delete = AsyncMock(side_effect=RecordNotFound)

        # When, Then
        review_pk = (uuid4(), uuid4())
        with pytest.raises(ReviewNotFound):
            await self.service.delete_review(*review_pk)
