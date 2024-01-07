# mypy: disable-error-code="method-assign"
import datetime
from unittest import IsolatedAsyncioTestCase
from app.models.stores import Store, StoreCreate
from uuid import uuid4
from unittest.mock import AsyncMock, Mock
import pytest
from app.repositories.stores import StoresRepository


class TestStoresRepository(IsolatedAsyncioTestCase):
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
        self.stores_repository = StoresRepository(self.async_session)

    @pytest.mark.asyncio
    async def test_save_should_save_store_to_db(self) -> None:
        # Given
        self.stores_repository.save = AsyncMock(return_value=self.store)
        Store.model_validate = Mock(return_value=self.store)
        # When
        saved_record = await self.stores_repository.create(self.store_create)
        # Then
        assert saved_record == self.store
        Store.model_validate.assert_called_once_with(self.store_create)
        self.stores_repository.save.assert_called_once_with(self.store)
