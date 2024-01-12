import datetime
from unittest import IsolatedAsyncioTestCase
from app.models.stores import Store, StoreCreate
from uuid import uuid4
from unittest.mock import AsyncMock
import pytest
from app.services.stores import StoresService


class TestStoresService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.store_create = StoreCreate(
            name="test",
            description="test",
            delivery_range_km=10,
        )
        self.store = Store(
            id=uuid4(),
            created_at=datetime.datetime(2023, 1, 1),
            updated_at=datetime.datetime(2023, 1, 1),
            **self.store_create.__dict__
        )
        self.async_session = AsyncMock()
        self.stores_repository = StoresService(self.async_session)
        self.repository = AsyncMock()
        self.service = StoresService(self.repository)

    @pytest.mark.asyncio
    async def test_create_store_should_call_repository_save(self) -> None:
        # Given
        self.repository.create = AsyncMock(return_value=self.store)
        # When
        saved_record = await self.service.create_store(self.store_create)
        # Then
        assert saved_record == self.store
        self.repository.create.assert_called_once_with(self.store_create)

    @pytest.mark.asyncio
    async def test_get_stores_should_call_repository_get_all(self) -> None:
        # Given
        self.repository.get_all = AsyncMock(return_value=self.store)
        # When
        fetched_record = await self.service.get_stores(1, 1)
        # Then
        assert fetched_record == self.store
        self.repository.get_all.assert_called_once_with(skip=1, limit=1)

    @pytest.mark.asyncio
    async def test_count_stores_should_call_repository_count_all(self) -> None:
        # Given
        self.repository.count_all = AsyncMock(return_value=1)
        # When
        fetched_record = await self.service.count_stores()
        # Then
        assert fetched_record == 1
        self.repository.count_all.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_store_by_id_should_call_repository_get_by_id(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)
        # When
        fetched_record = await self.service.get_store_by_id("1")
        # Then
        assert fetched_record == self.store
        self.repository.get_by_id.assert_called_once_with("1")
