from typing import AsyncGenerator, Generator
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
from app.exceptions.addresses import NonExistentAddress

from app.exceptions.users import InvalidToken
from app.models.util import Coordinates, Id
from app.db import engine
from app.main import app


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


class BaseAPITestCase(BaseDbTestCase):
    client: AsyncClient

    @pytest.fixture(autouse=True)
    async def setup_api(self) -> AsyncGenerator[None, None]:
        transport = ASGITransport(app=app)  # type: ignore
        self.client = AsyncClient(transport=transport, base_url="http://test", headers=self.headers)
        yield
        await self.client.aclose()

    @pytest.fixture(autouse=True)
    def mock_auth(self) -> Generator[None, None, None]:
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
            self.headers = {"Authorization": f"Bearer {user_token}"}
            self.user_id = user_id
            yield

    @pytest.fixture
    def mock_auth_error(self, mock_auth: None) -> Generator[None, None, None]:
        """
        Mocks a server authentication error.
        """
        # Added mock_auth as a dependency in the function signature to make sure it is called before
        # this one and we override the mock and headers
        with patch("app.services.users.UsersService.validate_user") as mock:
            mock.side_effect = InvalidToken
            self.headers = {}
            yield

    @pytest.fixture
    def mock_google_maps(self) -> Generator[None, None, None]:
        with patch("app.services.addresses.AddressesService.get_address_coordinates") as mock:
            mock.return_value = Coordinates(latitude=0, longitude=0)
            yield

    @pytest.fixture
    def mock_google_maps_error(self) -> Generator[None, None, None]:
        with patch("app.services.addresses.AddressesService.get_address_coordinates") as mock:
            mock.side_effect = NonExistentAddress
            yield
