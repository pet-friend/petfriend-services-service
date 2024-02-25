from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
import httpx
from pytest_httpx import HTTPXMock

from app.config import settings
from app.exceptions.services import ServiceNotFound
from app.models.addresses import Address
from app.repositories.services import ServicesRepository
from app.services.addresses import AddressesService
from app.repositories.addresses import AddressesRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.addresses import AddressNotFound, AddressAlreadyExists, NonExistentAddress
from tests.factories.address_factories import AddressCreateFactory


class TestAddressesService:
    def setup_method(self) -> None:
        self.address_create = AddressCreateFactory.build(country_code="AR", type="other")
        self.repository = AsyncMock(spec=AddressesRepository)
        self.services_repository = AsyncMock(spec=ServicesRepository)

        self.service = AddressesService(self.repository, self.services_repository)
        self.google_maps_url = httpx.URL(
            settings.GOOGLE_MAPS_URL,
            params={
                "key": settings.GOOGLE_MAPS_API_KEY,
                "address": self.service._get_text_address(self.address_create),
            },
        )

    @pytest.mark.asyncio
    async def test_create_address_should_call_repository_save(self, httpx_mock: HTTPXMock) -> None:
        # Given
        self.services_repository.get_by_id.return_value = object()
        self.repository.get_by_id.return_value = None
        self.repository.save.side_effect = lambda x: x
        service_id = uuid4()

        lat = -34.6036844
        long = -58.3815591
        httpx_mock.add_response(
            url=self.google_maps_url,
            json={
                "status": "OK",
                "results": [{"geometry": {"location": {"lat": lat, "lng": long}}}],
            },
        )

        # When
        saved_record = await self.service.create_address(service_id, self.address_create)

        # Then
        assert saved_record.id == service_id
        assert self.address_create.model_dump().items() < saved_record.model_dump().items()
        assert saved_record.latitude == lat
        assert saved_record.longitude == long
        self.repository.save.assert_called_once_with(saved_record)

    @pytest.mark.asyncio
    async def test_create_address_twice_should_raise(self) -> None:
        # Given
        service_id = uuid4()
        address = Address(id=service_id, **self.address_create.model_dump())
        self.repository.get_by_id.return_value = address
        self.services_repository.get_by_id.return_value = object()

        # When, Then
        with pytest.raises(AddressAlreadyExists):
            await self.service.create_address(service_id, self.address_create)

    @pytest.mark.asyncio
    async def test_create_address_no_service_should_raise(self) -> None:
        # Given
        service_id = uuid4()
        address = Address(id=service_id, **self.address_create.model_dump())
        self.repository.get_by_id.return_value = address
        self.services_repository.get_by_id.return_value = None

        # When, Then
        with pytest.raises(ServiceNotFound):
            await self.service.create_address(service_id, self.address_create)

    @pytest.mark.asyncio
    async def test_get_address_should_call_repository_get_by_id(self) -> None:
        # Given
        service_id = uuid4()
        address = Address(id=service_id, **self.address_create.model_dump())
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
        with pytest.raises(AddressNotFound):
            await self.service.get_address(uuid4())

    @pytest.mark.asyncio
    async def test_update_address_should_call_repository_update(
        self, httpx_mock: HTTPXMock
    ) -> None:
        # Given
        service_id = uuid4()
        address = Address(id=service_id, **self.address_create.model_dump())
        self.repository.update.side_effect = lambda _id, record: address

        lat = 1.5
        long = 2.5
        httpx_mock.add_response(
            url=self.google_maps_url,
            json={
                "status": "OK",
                "results": [{"geometry": {"location": {"lat": lat, "lng": long}}}],
            },
        )

        # When
        saved_record = await self.service.update_address(service_id, self.address_create)

        # Then
        assert saved_record == address
        data = self.address_create.model_dump()
        data["latitude"] = lat
        data["longitude"] = long
        self.repository.update.assert_called_once_with(service_id, data)

    @pytest.mark.asyncio
    async def test_delete_address_should_call_repository_delete(self) -> None:
        # Given
        service_id = uuid4()

        # When
        await self.service.delete_address(service_id)

        # Then
        self.repository.delete.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_update_address_not_exists_should_raise(self, httpx_mock: HTTPXMock) -> None:
        # Given
        service_id = uuid4()
        self.repository.update.side_effect = RecordNotFound()
        httpx_mock.add_response(
            url=self.google_maps_url,
            json={
                "status": "OK",
                "results": [{"geometry": {"location": {"lat": 1.5, "lng": 2.5}}}],
            },
        )

        # When, Then
        with pytest.raises(AddressNotFound):
            await self.service.update_address(service_id, self.address_create)

    @pytest.mark.asyncio
    async def test_delete_address_not_exists_should_raise(self) -> None:
        # Given
        service_id = uuid4()
        self.repository.delete.side_effect = RecordNotFound()

        # When, Then
        with pytest.raises(AddressNotFound):
            await self.service.delete_address(service_id)

    @pytest.mark.asyncio
    async def test_create_invalid_address_should_raise(self, httpx_mock: HTTPXMock) -> None:
        # Given
        self.repository.get_by_id.return_value = None
        self.repository.save.side_effect = lambda x: x
        service_id = uuid4()

        httpx_mock.add_response(
            url=self.google_maps_url,
            json={
                "status": "ZERO_RESULTS",
                "results": [],
            },
        )

        # When, Then
        with pytest.raises(NonExistentAddress):
            await self.service.create_address(service_id, self.address_create)
