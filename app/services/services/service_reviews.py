from fastapi import Depends
from datetime import datetime, timezone

from app.exceptions.reviews import ReviewRequirementsNotMet
from app.models.reviews import ReviewCreate
from app.models.services import ServiceReview
from app.models.payments import PaymentStatus
from app.models.util import Id
from app.repositories.reviews import ServiceReviewsRepository
from .appointments import AppointmentsService
from ..reviews import ReviewsService


class ServiceReviewsService(ReviewsService[ServiceReview, Id, Id]):
    def __init__(
        self,
        repository: ServiceReviewsRepository = Depends(),
        appointments_service: AppointmentsService = Depends(),
    ):
        super().__init__(repository)
        self.appointments_service = appointments_service

    async def create_review(
        self, data: ReviewCreate, service_id: Id, reviewer_id: Id, *, now: datetime | None = None
    ) -> ServiceReview:
        await self._check_already_exists(service_id, reviewer_id)

        now = now or datetime.now(timezone.utc)
        # Only allow reviews for appointments that have at least started by now
        appointments = await self.appointments_service.get_appointments(
            before=now,
            include_partial=True,
            customer_id=reviewer_id,
            service_id=service_id,
            payment_status=PaymentStatus.COMPLETED,
        )
        if len(appointments) == 0:
            raise ReviewRequirementsNotMet

        return await self.repository.save(
            ServiceReview(**data.model_dump(), service_id=service_id, reviewer_id=reviewer_id)
        )
