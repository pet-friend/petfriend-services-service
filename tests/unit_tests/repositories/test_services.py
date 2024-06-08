# mypy: disable-error-code="method-assign"
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from sqlalchemy import ScalarResult

from app.models.addresses import Address
from app.models.services import Service
from app.models.services.appointment_slots import AppointmentSlots
from app.repositories.services import ServicesRepository
from tests.factories.service_factories import ServiceCreateFactory


class TestServicesRepository:
    def setup_method(self) -> None:
        self.service_create = ServiceCreateFactory.build()
        service_id = uuid4()
        self.service = Service(
            id=service_id,
            owner_id=uuid4(),
            address=Address(latitude=0, longitude=0, **self.service_create.address.model_dump()),
            appointment_slots=[
                AppointmentSlots(service_id=service_id, **slot_create.model_dump())
                for slot_create in self.service_create.appointment_slots
            ],
            **self.service_create.model_dump(exclude={"address", "appointment_slots"})
        )
        self.async_session = AsyncMock()
        self.services_repository = ServicesRepository(self.async_session)

    async def test_count_all_should_return_count_of_services(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=1)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.services_repository.count_all()

        # Then
        assert count == 1

    async def test_count_all_should_return_count_of_services_with_filters(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=1)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.services_repository.count_all(name="test")

        # Then
        assert count == 1

    async def test_count_all_should_return_zero_if_no_services(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=0)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.services_repository.count_all()

        # Then
        assert count == 0

    async def test_count_all_should_return_zero_if_no_services_with_filters(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=0)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.services_repository.count_all(name="test")

        # Then
        assert count == 0
