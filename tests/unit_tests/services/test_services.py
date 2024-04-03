from typing import Any, Generator
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.services import ServiceNotFound
from app.exceptions.users import Forbidden
from app.models.services import Service, AppointmentSlots
from app.models.addresses import Address
from app.repositories.services import ServicesRepository
from app.services.services import ServicesService
from tests.factories.service_factories import ServiceCreateFactory
from tests.util import CustomMatcher


class TestServicesService:
    def setup_method(self) -> None:
        self.service_create = ServiceCreateFactory().build()

        self.owner_id = uuid4()
        service_id = uuid4()
        self.service_model = Service(
            id=service_id,
            owner_id=self.owner_id,
            appointment_slots=[
                AppointmentSlots(service_id=service_id, **slot_create.model_dump())
                for slot_create in self.service_create.appointment_slots
            ],
            address=Address(latitude=0, longitude=0, **self.service_create.address.model_dump()),
            **self.service_create.model_dump(exclude={"address", "appointment_slots"})
        )

        self.async_session = AsyncMock()
        self.repository = AsyncMock(spec=ServicesRepository)
        self.service = ServicesService(self.repository, AsyncMock())

    @pytest.fixture
    def mock_get_address(self) -> Generator[AsyncMock, None, None]:
        with patch("app.services.addresses.AddressesService.get_address") as mock:
            mock.return_value = Address(
                latitude=0, longitude=0, **self.service_create.address.model_dump()
            )
            yield mock

    async def test_create_service_should_call_repository_save(
        self, mock_get_address: AsyncMock
    ) -> None:
        # Given
        self.repository.save = AsyncMock(return_value=self.service_model)
        self.repository.get_by_name = AsyncMock(return_value=None)

        # When
        saved_record = await self.service.create_service(self.service_create, self.owner_id)

        # Then
        assert saved_record == self.service_model

        def check_save(service: Service) -> None:
            assert service.owner_id == self.owner_id
            assert (
                service.model_dump().items()
                >= self.service_create.model_dump(exclude={"address", "appointment_slots"}).items()
            )
            assert (
                service.address.model_dump().items()
                >= self.service_create.address.model_dump().items()
            )
            assert len(service.appointment_slots) == len(self.service_create.appointment_slots)
            assert all(
                any(
                    s.start_time == s_create.start_time
                    and s.end_time == s_create.end_time
                    and s.appointment_duration == s_create.appointment_duration
                    and s.day_of_week == s_create.day_of_week
                    for s in service.appointment_slots
                )
                for s_create in self.service_create.appointment_slots
            )

        self.repository.save.assert_called_once_with(CustomMatcher(check_save))
        mock_get_address.assert_called_once_with(self.service_create.address)

    async def test_get_services_should_call_repository_get_all(self) -> None:
        # Given
        self.repository.get_all = AsyncMock(return_value=self.service_model)

        # When
        fetched_record = await self.service.get_services(1, 1)

        # Then
        assert fetched_record == self.service_model
        self.repository.get_all.assert_called_once_with(skip=1, limit=1)

    async def test_get_services_by_owner_should_call_repository_get_all_with_owner_id(self) -> None:
        # Given
        self.repository.get_all = AsyncMock(return_value=self.service_model)

        # When
        fetched_record = await self.service.get_services(1, 1, owner_id=self.owner_id)

        # Then
        assert fetched_record == self.service_model
        self.repository.get_all.assert_called_once_with(skip=1, limit=1, owner_id=self.owner_id)

    async def test_count_services_should_call_repository_count_all(self) -> None:
        # Given
        self.repository.count_all = AsyncMock(return_value=1)

        # When
        fetched_record = await self.service.count_services()

        # Then
        assert fetched_record == 1
        self.repository.count_all.assert_called_once_with()

    async def test_get_service_by_id_should_call_repository_get_by_id(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.service_model)

        # When
        fetched_record = await self.service.get_service_by_id(self.service_model.id)

        # Then
        assert fetched_record == self.service_model
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)

    async def test_update_service_should_call_repository_update(
        self, mock_get_address: AsyncMock
    ) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.service_model)
        self.repository.update = AsyncMock(return_value=self.service_model)

        # When
        fetched_record = await self.service.update_service(
            self.service_model.id, self.service_create, self.owner_id
        )

        # Then
        assert fetched_record == self.service_model

        def check_update(update: dict[str, Any]) -> None:
            assert (
                update.items()
                >= self.service_create.model_dump(exclude={"address", "appointment_slots"}).items()
            )
            assert update["address"] == mock_get_address.return_value
            assert len(update["appointment_slots"]) == len(self.service_create.appointment_slots)
            assert all(
                any(
                    s.start_time == s_create.start_time
                    and s.end_time == s_create.end_time
                    and s.appointment_duration == s_create.appointment_duration
                    and s.day_of_week == s_create.day_of_week
                    for s in update["appointment_slots"]
                )
                for s_create in self.service_create.appointment_slots
            )

        self.repository.update.assert_called_once_with(
            self.service_model.id, CustomMatcher(check_update)
        )
        mock_get_address.assert_called_once_with(self.service_create.address)

    async def test_cant_update_service_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.service_model)

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_service(self.service_model.id, self.service_create, uuid4())

        # Then
        self.repository.update.assert_not_called()

    async def test_update_inexistent_service_should_raise_service_not_found(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=None)

        # When
        with pytest.raises(ServiceNotFound):
            await self.service.update_service(
                self.service_model.id, self.service_create, self.owner_id
            )

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)

    async def test_delete_service_should_call_repository_delete(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.service_model)
        self.repository.delete = AsyncMock(return_value=None)
        # self.service.files_service.delete_file = AsyncMock(return_value=None)

        # When
        await self.service.delete_service(self.service_model.id, self.owner_id)

        # Then
        self.repository.delete.assert_called_once_with(self.service_model.id)
        # self.service.files_service.delete_file.assert_called_once_with(self.service_model.id)

    async def test_cant_delete_service_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.service_model)
        # self.service.files_service.delete_file = AsyncMock(return_value=None)

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.delete_service(self.service_model.id, uuid4())

        # Then
        self.repository.delete.assert_not_called()
        # self.service.files_service.delete_file.assert_not_called()

    async def test_delete_inexistent_service_should_raise_service_not_found(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=None)
        # self.service.files_service.delete_file = AsyncMock(return_value=None)

        # When
        with pytest.raises(ServiceNotFound):
            await self.service.delete_service(self.service_model.id, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)

    async def test_delete_service_without_image_should_ignore_file_not_found(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.service_model)
        self.repository.delete = AsyncMock(return_value=None)
        # self.service.files_service.delete_file = AsyncMock(side_effect=FileNotFoundError)

        # When
        await self.service.delete_service(self.service_model.id, self.owner_id)

        # Then
        self.repository.delete.assert_called_once_with(self.service_model.id)
        # self.service.files_service.delete_file.assert_called_once_with(self.service_model.id)
