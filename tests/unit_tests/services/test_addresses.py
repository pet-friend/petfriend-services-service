import pytest
import httpx
from pytest_httpx import HTTPXMock

from app.config import settings
from app.models.addresses import AddressRead
from app.services.addresses import AddressesService
from app.exceptions.addresses import NonExistentAddress
from tests.factories.address_factories import AddressCreateFactory


class TestAddressesService:
    def setup_method(self) -> None:
        self.address_create = AddressCreateFactory.build(country_code="AR", type="other")

        self.google_maps_url = httpx.URL(
            settings.GOOGLE_MAPS_URL,
            params={
                "key": settings.GOOGLE_MAPS_API_KEY,
                "address": AddressesService._get_text_address(self.address_create),
            },
        )

    async def test_get_address_returns_valid_lat_long(self, httpx_mock: HTTPXMock) -> None:
        # Given
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
        saved_record = await AddressesService.get_address(self.address_create)

        # Then
        assert saved_record is not None
        assert AddressRead(**saved_record.model_dump()) == AddressRead(
            **self.address_create.model_dump(), latitude=lat, longitude=long
        )

    async def test_get_invalid_address_should_raise(self, httpx_mock: HTTPXMock) -> None:
        # Given
        httpx_mock.add_response(
            url=self.google_maps_url,
            json={
                "status": "ZERO_RESULTS",
                "results": [],
            },
        )

        # When, Then
        with pytest.raises(NonExistentAddress):
            await AddressesService.get_address(self.address_create)
