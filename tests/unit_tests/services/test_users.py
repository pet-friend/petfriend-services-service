from uuid import uuid4

import pytest
from pytest_httpx import HTTPXMock

from app.config import settings
from app.exceptions.users import InvalidToken
from app.services.users import UsersService


class TestUserService:
    def setup_method(self) -> None:
        self.users_service = UsersService()
        self.token = "token :D"

    @pytest.mark.asyncio
    async def test_user_id_is_valid(self, httpx_mock: HTTPXMock) -> None:
        # Given
        user_id = uuid4()
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/validate",
            method="POST",
            json={"user_id": str(user_id)},
            match_headers={"Authorization": f"Bearer {self.token}"},
        )

        # When
        result_id = await self.users_service.validate_user(self.token)

        # Then
        assert result_id == user_id

    @pytest.mark.asyncio
    async def test_user_id_is_not_valid(self, httpx_mock: HTTPXMock) -> None:
        # Given
        httpx_mock.add_response(
            url=f"{settings.USERS_SERVICE_URL}/validate",
            method="POST",
            status_code=401,
            match_headers={"Authorization": f"Bearer {self.token}"},
        )

        # When, Then
        with pytest.raises(InvalidToken):
            await self.users_service.validate_user(self.token)
