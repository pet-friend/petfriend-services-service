from unittest import IsolatedAsyncioTestCase
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import text
from httpx import AsyncClient

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

    def setUp(self) -> None:
        super().setUp()
        self.client = AsyncClient(app=app, base_url="http://test")

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()
        await self.client.aclose()
