import datetime
from unittest import IsolatedAsyncioTestCase
from app.exceptions.repository import RecordNotFound
from app.exceptions.stores import StoreAlreadyExists, StoreNotFound
from app.models.stores import Store, StoreCreate
from uuid import uuid4
from unittest.mock import AsyncMock
import pytest
from app.repositories.stores import StoresRepository
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
        self.repository = AsyncMock(spec=StoresRepository)
        self.service = StoresService(self.repository)

    @pytest.mark.asyncio
    async def test_create_store_should_call_repository_save(self) -> None:
        # Given
        self.repository.create = AsyncMock(return_value=self.store)
        self.repository.get_by_name = AsyncMock(return_value=None)
        # When
        saved_record = await self.service.create_store(self.store_create)
        # Then
        assert saved_record == self.store
        self.repository.create.assert_called_once_with(self.store_create)

    @pytest.mark.asyncio
    async def test_create_store_with_existing_name_should_raise_store_already_exists(self) -> None:
        # Given
        self.repository.get_by_name = AsyncMock(return_value=self.store)
        # When
        with pytest.raises(StoreAlreadyExists):
            await self.service.create_store(self.store_create)
        # Then
        self.repository.get_by_name.assert_called_once_with(self.store_create.name)

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

    @pytest.mark.asyncio
    async def test_update_store_should_call_repository_update(self) -> None:
        # Given
        self.repository.update = AsyncMock(return_value=self.store)
        # When
        fetched_record = await self.service.update_store("1", self.store_create)  # type: ignore
        # Then
        assert fetched_record == self.store
        self.repository.update.assert_called_once_with("1", self.store_create.__dict__)

    @pytest.mark.asyncio
    async def test_update_inexistent_store_should_raise_store_not_found(self) -> None:
        # Given
        self.repository.update = AsyncMock(side_effect=RecordNotFound)
        # When
        with pytest.raises(StoreNotFound):
            await self.service.update_store("1", self.store_create)  # type: ignore
        # Then
        self.repository.update.assert_called_once_with("1", self.store_create.__dict__)

    @pytest.mark.asyncio
    async def test_delete_store_should_call_repository_delete(self) -> None:
        # Given
        self.repository.delete = AsyncMock(return_value=None)
        self.service.files_service.delete_file = AsyncMock(return_value=None)  # type: ignore
        # When
        fetched_record = await self.service.delete_store("1")  # type: ignore
        # Then
        assert fetched_record is None
        self.repository.delete.assert_called_once_with("1")
        self.service.files_service.delete_file.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_delete_inexistent_store_should_raise_store_not_found(self) -> None:
        # Given
        self.repository.delete = AsyncMock(side_effect=RecordNotFound)
        self.service.files_service.delete_file = AsyncMock(return_value=None)  # type: ignore
        # When
        with pytest.raises(StoreNotFound):
            await self.service.delete_store("1")  # type: ignore
        # Then
        self.repository.delete.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_delete_store_without_image_should_ignore_file_not_found(self) -> None:
        # Given
        self.repository.delete = AsyncMock(return_value=None)
        self.service.files_service.delete_file = AsyncMock(  # type: ignore
            side_effect=FileNotFoundError
        )
        # When
        fetched_record = await self.service.delete_store("1")  # type: ignore
        # Then
        assert fetched_record is None
        self.repository.delete.assert_called_once_with("1")
        self.service.files_service.delete_file.assert_called_once_with("1")
