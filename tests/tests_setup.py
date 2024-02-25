from typing import Generator
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
from app.exceptions.addresses import NonExistentAddress

from app.exceptions.users import InvalidToken
from app.models.util import Id
from app.db import engine
from app.main import app


class BaseDbTestCase(IsolatedAsyncioTestCase):
    db: AsyncSession

    def setUp(self) -> None:
        self.db = AsyncSession(bind=engine)

    async def asyncSetUp(self) -> None:
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.run_sync(SQLModel.metadata.create_all)

    async def asyncTearDown(self) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await self.db.close()


class BaseAPITestCase(BaseDbTestCase):
    client: AsyncClient

    @pytest.fixture(autouse=True)
    def mock_auth(self, request: pytest.FixtureRequest) -> Generator[None, None, None]:
        """
        Mocks the server authentication.
        """
        mock_auth = "noauth" not in request.keywords
        user_token = str(uuid4())
        user_id = uuid4()

        with patch("app.services.users.UsersService.validate_user") as mock:

            def check_token(token: str) -> Id:
                if token == user_token and mock_auth:
                    return user_id
                raise InvalidToken

            mock.side_effect = check_token

            self.headers = {"Authorization": f"Bearer {user_token}"} if mock_auth else {}
            self.user_id = user_id
            yield

    @pytest.fixture(autouse=True)
    def mock_google_maps(self, request: pytest.FixtureRequest) -> Generator[None, None, None]:
        """
        Mocks google maps requests
        """
        mock_lat_long = "invalidaddress" not in request.keywords

        with patch("app.services.addresses.AddressesService.get_address_coordinates") as mock:
            if mock_lat_long:
                mock.return_value = (0, 0)
            else:
                mock.side_effect = NonExistentAddress
            yield

    def setUp(self) -> None:
        super().setUp()
        transport = ASGITransport(app=app)  # type: ignore
        self.client = AsyncClient(transport=transport, base_url="http://test", headers=self.headers)

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()
        await self.client.aclose()
