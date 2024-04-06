from typing import AsyncGenerator, Generator, Protocol
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from pytest_httpx import HTTPXMock
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
from app.exceptions.addresses import NonExistentAddress

from app.exceptions.users import InvalidToken
from app.models.util import Coordinates, Id
from app.db import engine
from app.main import app
from app.config import settings


class BaseDbTestCase:
    db: AsyncSession

    @pytest.fixture(autouse=True)
    async def setup_db(self) -> AsyncGenerator[None, None]:
        self.db = AsyncSession(bind=engine)
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.run_sync(SQLModel.metadata.create_all)
            yield
            await conn.run_sync(SQLModel.metadata.drop_all)
        await self.db.close()


@pytest.mark.usefixtures("blob_setup")
class BaseAPITestCase(BaseDbTestCase):
    client: AsyncClient

    @pytest.fixture(autouse=True)
    async def setup_api(self) -> AsyncGenerator[None, None]:
        transport = ASGITransport(app=app)  # type: ignore
        self.client = AsyncClient(transport=transport, base_url="http://test", headers=self.headers)
        yield
        await self.client.aclose()

    @pytest.fixture(autouse=True)
    def mock_auth(self) -> Generator[AsyncMock, None, None]:
        """
        Mocks the server authentication.
        """
        user_token = str(uuid4())
        user_id = uuid4()

        with patch("app.services.users.UsersService.validate_user") as mock:

            def check_token(token: str) -> Id:
                if token == user_token:
                    return user_id
                raise InvalidToken

            mock.side_effect = check_token
            self.token = user_token
            self.headers = {"Authorization": f"Bearer {user_token}"}
            self.user_id = user_id
            yield mock

    @pytest.fixture
    def mock_auth_error(self, mock_auth: AsyncMock) -> Generator[AsyncMock, None, None]:
        """
        Mocks a server authentication error.
        """
        mock_auth.side_effect = InvalidToken
        yield mock_auth

    @pytest.fixture(autouse=True)
    def mock_get_cordinates(self) -> Generator[AsyncMock, None, None]:
        with patch("app.services.addresses.AddressesService.get_address_coordinates") as mock:
            mock.return_value = Coordinates(latitude=0, longitude=0)
            yield mock

    @pytest.fixture
    def mock_get_cordinates_error(
        self,
        mock_get_cordinates: AsyncMock,
    ) -> Generator[AsyncMock, None, None]:
        mock_get_cordinates.return_value = None
        mock_get_cordinates.side_effect = NonExistentAddress
        yield mock_get_cordinates

    @pytest.fixture
    def mock_get_user_coordinates(self, httpx_mock: HTTPXMock) -> "GetUserCoordinatesMock":
        def inner(
            address_id: Id,
            fail: bool = False,
            return_value: Coordinates = Coordinates(latitude=0, longitude=0),
        ) -> None:
            httpx_mock.add_response(
                method="GET",
                url=f"{settings.USERS_SERVICE_URL}/users/{self.user_id}/addresses/{address_id}",
                match_headers={"Authorization": f"Bearer {self.token}"},
                json=(return_value.model_dump() if not fail else None),
                status_code=200 if not fail else 404,
            )

        return inner


class GetUserCoordinatesMock(Protocol):
    def __call__(
        self,
        address_id: Id,
        fail: bool = False,
        return_value: Coordinates = Coordinates(latitude=0, longitude=0),
    ) -> None: ...
