from typing import AsyncGenerator
from uuid import uuid4
from httpx import AsyncClient, HTTPStatusError

import pytest
import pytest_asyncio
from pytest_httpx import HTTPXMock

from app.config import settings
from app.exceptions.addresses import AddressNotFound
from app.exceptions.users import InvalidToken
from app.services.users import Notification, UsersService


class TestUserService:
    def setup_method(self) -> None:
        self.token = "token :D"

    @pytest_asyncio.fixture(autouse=True, scope="function")
    async def users_service(self) -> AsyncGenerator[None, None]:
        async with AsyncClient(base_url=settings.USERS_SERVICE_URL) as client:
            self.service = UsersService(client)
            yield

    async def test_validate_user_id_is_valid(self, httpx_mock: HTTPXMock) -> None:
        # Given
        user_id = uuid4()
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/validate",
            method="POST",
            json={"user_id": str(user_id)},
            match_headers={"Authorization": f"Bearer {self.token}"},
        )

        # When
        result_id = await self.service.validate_user(self.token)

        # Then
        assert result_id == user_id

    async def test_validate_user_id_is_not_valid(self, httpx_mock: HTTPXMock) -> None:
        # Given
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/validate",
            method="POST",
            status_code=401,
            match_headers={"Authorization": f"Bearer {self.token}"},
        )

        # When, Then
        with pytest.raises(InvalidToken):
            await self.service.validate_user(self.token)

    async def test_get_coordinates_is_valid(self, httpx_mock: HTTPXMock) -> None:
        # Given
        user_id = uuid4()
        address_id = uuid4()
        lat = 1.0
        long = 8.0
        token = str(uuid4())
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/users/{user_id}/addresses/{address_id}",
            method="GET",
            json={"latitude": lat, "longitude": long},
            headers={"Authorization": f"Bearer {token}"},
        )

        # When
        coords = await self.service.get_user_address_coordinates(user_id, address_id, token)

        # Then
        assert coords.latitude == lat
        assert coords.longitude == long

    async def test_get_coordinates_not_found(self, httpx_mock: HTTPXMock) -> None:
        # Given
        user_id = uuid4()
        address_id = uuid4()
        token = str(uuid4())
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/users/{user_id}/addresses/{address_id}",
            method="GET",
            status_code=404,
            headers={"Authorization": f"Bearer {token}"},
        )

        # When, Then
        with pytest.raises(AddressNotFound):
            await self.service.get_user_address_coordinates(user_id, address_id, token)

    async def test_send_notification(self, httpx_mock: HTTPXMock) -> None:
        # Given
        user_id = uuid4()
        notification = Notification(source="purchase", title="title", message="message")
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/notifications/{user_id}",
            method="POST",
            match_json=notification.model_dump(),
            match_headers={"api-key": settings.NOTIFICATIONS_API_KEY},
        )

        # When
        await self.service.send_notification(user_id, notification)

    async def test_send_notification_error_should_not_raise(self, httpx_mock: HTTPXMock) -> None:
        # Given
        user_id = uuid4()
        notification = Notification(source="purchase", title="title", message="message")
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/notifications/{user_id}",
            method="POST",
            match_json=notification.model_dump(),
            match_headers={"api-key": settings.NOTIFICATIONS_API_KEY},
            status_code=500,
        )

        # When
        await self.service.send_notification(user_id, notification)

    async def test_send_notification_error_should_raise_if_param_true(
        self, httpx_mock: HTTPXMock
    ) -> None:
        # Given
        user_id = uuid4()
        notification = Notification(source="purchase", title="title", message="message")
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/notifications/{user_id}",
            method="POST",
            match_json=notification.model_dump(),
            match_headers={"api-key": settings.NOTIFICATIONS_API_KEY},
            status_code=500,
            json={"error": "error"},
        )

        # When, Then
        with pytest.raises(HTTPStatusError):
            await self.service.send_notification(user_id, notification, raise_on_error=True)
