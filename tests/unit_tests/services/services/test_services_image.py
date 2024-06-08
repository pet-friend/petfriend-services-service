# mypy: disable-error-code="method-assign"
from unittest.mock import AsyncMock
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

import pytest

from app.exceptions.services import ServiceNotFound
from app.exceptions.users import Forbidden
from app.models.addresses import Address
from app.models.services import Service, AppointmentSlots
from app.services.files import FilesService
from app.services.services import ServicesService
from app.repositories.services import ServicesRepository
from tests.factories.service_factories import ServiceCreateFactory
from ..util import File


@pytest.mark.usefixtures("blob_setup")
class TestServicesService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.service_create = ServiceCreateFactory.build()
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

        self.repository = AsyncMock(spec=ServicesRepository)
        self.files_service = AsyncMock(spec=FilesService)
        self.service = ServicesService(self.repository, self.files_service)
        self.file = File(open("tests/assets/test_image.jpg", "rb"))

    def tearDown(self) -> None:
        self.file.file.close()

    async def test_create_image_fail_if_service_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ServiceNotFound):
            await self.service.create_service_image(self.service_model.id, self.file, self.owner_id)

        self.repository.get_by_id.assert_called_once_with(self.service_model.id)

    async def test_set_image_fail_if_service_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ServiceNotFound):
            await self.service.set_service_image(self.service_model.id, self.file, self.owner_id)

        self.repository.get_by_id.assert_called_once_with(self.service_model.id)

    async def test_delete_image_fail_if_service_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ServiceNotFound):
            await self.service.delete_service_image(self.service_model.id, self.owner_id)

        self.repository.get_by_id.assert_called_once_with(self.service_model.id)

    async def test_create_image_calls_create_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.service_model

        # When
        await self.service.create_service_image(self.service_model.id, self.file, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)
        self.files_service.create_file.assert_called_once_with(self.service_model.id, self.file)

    async def test_cant_create_image_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.service_model

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.create_service_image(self.service_model.id, self.file, uuid4())

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)
        self.files_service.create_file.assert_not_called()

    async def test_set_image_calls_set_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.service_model

        # When
        await self.service.set_service_image(self.service_model.id, self.file, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)
        self.files_service.set_file.assert_called_once_with(self.service_model.id, self.file)

    async def test_cant_set_image_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.service_model

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.set_service_image(self.service_model.id, self.file, uuid4())

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)
        self.files_service.set_file.assert_not_called()

    async def test_delete_image_calls_delete_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.service_model

        # When
        await self.service.delete_service_image(self.service_model.id, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)
        self.files_service.delete_file.assert_called_once_with(self.service_model.id)

    async def test_cant_delete_image_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.service_model

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.delete_service_image(self.service_model.id, uuid4())

        # Then
        self.repository.get_by_id.assert_called_once_with(self.service_model.id)
        self.files_service.delete_file.assert_not_called()
