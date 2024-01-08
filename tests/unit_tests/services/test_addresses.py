from uuid import uuid4
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

import pytest

from app.models.addresses import Address
from app.services.addresses import AddressesService
from app.repositories.addresses import AddressesRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.addresses import AddressNotFound, AddressAlreadyExists
from tests.factories.address_factories import AddressCreateFactory


class TestAddressesService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.address_create = AddressCreateFactory.build(country_code="AR", type="other")
        self.repository = AsyncMock(spec=AddressesRepository)

        self.service = AddressesService(self.repository)

    @pytest.mark.asyncio
    async def test_create_address_should_call_repository_save(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None
        self.repository.save.side_effect = lambda x: x
        service_id = uuid4()

        # When
        saved_record = await self.service.create_address(service_id, self.address_create)

        # Then
        assert saved_record.id == service_id
        assert self.address_create.model_dump().items() < saved_record.model_dump().items()
        self.repository.save.assert_called_once_with(saved_record)

    @pytest.mark.asyncio
    async def test_create_address_twice_should_raise(self) -> None:
        # Given
        service_id = uuid4()
        address = Address(service_id=service_id, **self.address_create.model_dump())
        self.repository.get_by_id.return_value = address

        # When, Then
        with self.assertRaises(AddressAlreadyExists):
            await self.service.create_address(service_id, self.address_create)

    @pytest.mark.asyncio
    async def test_get_address_should_call_repository_get_by_id(self) -> None:
        # Given
        service_id = uuid4()
        address = Address(service_id=service_id, **self.address_create.model_dump())
        self.repository.get_by_id.return_value = address

        # When
        saved_record = await self.service.get_address(service_id)

        # Then
        assert saved_record == address
        self.repository.get_by_id.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_get_address_invalid_address_should_raise_exception(self) -> None:
        # Given
        self.repository.get_by_id.side_effect = AddressNotFound()

        # When, Then
        with self.assertRaises(AddressNotFound):
            await self.service.get_address(uuid4())

    @pytest.mark.asyncio
    async def test_update_address_should_call_repository_update(self) -> None:
        # Given
        service_id = uuid4()
        address = Address(service_id=service_id, **self.address_create.model_dump())
        self.repository.update.side_effect = lambda _id, record: address

        # When
        saved_record = await self.service.update_address(service_id, self.address_create)

        # Then
        assert saved_record == address
        self.repository.update.assert_called_once_with(service_id, self.address_create.model_dump())

    @pytest.mark.asyncio
    async def test_delete_address_should_call_repository_delete(self) -> None:
        # Given
        service_id = uuid4()

        # When
        await self.service.delete_address(service_id)

        # Then
        self.repository.delete.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_update_address_not_exists_should_raise(self) -> None:
        # Given
        service_id = uuid4()
        self.repository.update.side_effect = RecordNotFound()

        # When, Then
        with self.assertRaises(AddressNotFound):
            await self.service.update_address(service_id, self.address_create)

    @pytest.mark.asyncio
    async def test_delete_address_not_exists_should_raise(self) -> None:
        # Given
        service_id = uuid4()
        self.repository.delete.side_effect = RecordNotFound()

        # When, Then
        with self.assertRaises(AddressNotFound):
            await self.service.delete_address(service_id)
