from typing import Generator
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.stores import StoreAlreadyExists, StoreNotFound
from app.exceptions.users import Forbidden
from app.models.stores import Store
from app.models.addresses import Address
from app.repositories.stores import StoresRepository
from app.services.stores import StoresService
from tests.factories.store_factories import StoreCreateFactory
from tests.util import CustomMatcher


class TestStoresService:
    def setup_method(self) -> None:
        self.store_create = StoreCreateFactory().build()

        self.owner_id = uuid4()
        self.store = Store(
            owner_id=self.owner_id,
            address=Address(latitude=0, longitude=0, **self.store_create.address.model_dump()),
            **self.store_create.model_dump(exclude={"address"})
        )

        self.async_session = AsyncMock()
        self.repository = AsyncMock(spec=StoresRepository)
        self.service = StoresService(self.repository)

    @pytest.fixture
    def mock_get_address(self) -> Generator[AsyncMock, None, None]:
        with patch("app.services.addresses.AddressesService.get_address") as mock:
            mock.return_value = Address(
                latitude=0, longitude=0, **self.store_create.address.model_dump()
            )
            yield mock

    async def test_create_store_should_call_repository_save(
        self, mock_get_address: AsyncMock
    ) -> None:
        # Given
        self.repository.save = AsyncMock(return_value=self.store)
        self.repository.get_by_name = AsyncMock(return_value=None)

        # When
        saved_record = await self.service.create_store(self.store_create, self.owner_id)

        # Then
        assert saved_record == self.store

        def check_save(store: Store) -> None:
            assert store.owner_id == self.owner_id
            assert (
                store.model_dump().items()
                >= self.store_create.model_dump(exclude={"address"}).items()
            )
            assert (
                store.address.model_dump().items() >= self.store_create.address.model_dump().items()
            )

        self.repository.save.assert_called_once_with(CustomMatcher(check_save))
        mock_get_address.assert_called_once_with(self.store_create.address)

    async def test_create_store_with_existing_name_should_raise_store_already_exists(self) -> None:
        # Given
        self.repository.get_by_name = AsyncMock(return_value=self.store)

        # When
        with pytest.raises(StoreAlreadyExists):
            await self.service.create_store(self.store_create, self.owner_id)

        # Then
        self.repository.get_by_name.assert_called_once_with(self.store_create.name)

    async def test_get_stores_should_call_repository_get_all(self) -> None:
        # Given
        self.repository.get_all = AsyncMock(return_value=self.store)
        # When
        fetched_record = await self.service.get_stores(1, 1)
        # Then
        assert fetched_record == self.store
        self.repository.get_all.assert_called_once_with(skip=1, limit=1)

    async def test_get_stores_by_owner_should_call_repository_get_all_with_owner_id(self) -> None:
        # Given
        self.repository.get_all = AsyncMock(return_value=self.store)
        # When
        fetched_record = await self.service.get_stores(1, 1, owner_id=self.owner_id)
        # Then
        assert fetched_record == self.store
        self.repository.get_all.assert_called_once_with(skip=1, limit=1, owner_id=self.owner_id)

    async def test_count_stores_should_call_repository_count_all(self) -> None:
        # Given
        self.repository.count_all = AsyncMock(return_value=1)
        # When
        fetched_record = await self.service.count_stores()
        # Then
        assert fetched_record == 1
        self.repository.count_all.assert_called_once_with()

    async def test_get_store_by_id_should_call_repository_get_by_id(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)
        # When
        fetched_record = await self.service.get_store_by_id("1")
        # Then
        assert fetched_record == self.store
        self.repository.get_by_id.assert_called_once_with("1")

    async def test_update_store_should_call_repository_update(
        self, mock_get_address: AsyncMock
    ) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)
        self.repository.update = AsyncMock(return_value=self.store)

        # When
        fetched_record = await self.service.update_store(
            "1", self.store_create, self.owner_id  # type: ignore
        )

        # Then
        assert fetched_record == self.store
        expected_update = self.store_create.model_dump(exclude={"address"})
        expected_update["address"] = mock_get_address.return_value
        self.repository.update.assert_called_once_with("1", expected_update)
        mock_get_address.assert_called_once_with(self.store_create.address)

    async def test_cant_update_store_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_store("1", self.store_create, uuid4())  # type: ignore

        # Then
        self.repository.update.assert_not_called()

    async def test_update_inexistent_store_should_raise_store_not_found(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=None)

        # When
        with pytest.raises(StoreNotFound):
            await self.service.update_store("1", self.store_create, self.owner_id)  # type: ignore

        # Then
        self.repository.get_by_id.assert_called_once_with("1")

    async def test_delete_store_should_call_repository_delete(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)
        self.repository.delete = AsyncMock(return_value=None)
        self.service.files_service.delete_file = AsyncMock(return_value=None)  # type: ignore

        # When
        fetched_record = await self.service.delete_store("1", self.owner_id)  # type: ignore

        # Then
        assert fetched_record is None
        self.repository.delete.assert_called_once_with("1")
        self.service.files_service.delete_file.assert_called_once_with("1")

    async def test_cant_delete_store_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)
        self.service.files_service.delete_file = AsyncMock(return_value=None)  # type: ignore

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.delete_store("1", uuid4())  # type: ignore

        # Then
        self.repository.delete.assert_not_called()
        self.service.files_service.delete_file.assert_not_called()

    async def test_delete_inexistent_store_should_raise_store_not_found(self) -> None:
        # Given
        # self.repository.delete = AsyncMock(side_effect=RecordNotFound)
        self.repository.get_by_id = AsyncMock(return_value=None)
        self.service.files_service.delete_file = AsyncMock(return_value=None)  # type: ignore

        # When
        with pytest.raises(StoreNotFound):
            await self.service.delete_store("1", self.owner_id)  # type: ignore

        # Then
        # self.repository.delete.assert_called_once_with("1")
        self.repository.get_by_id.assert_called_once_with("1")

    async def test_delete_store_without_image_should_ignore_file_not_found(self) -> None:
        # Given
        self.repository.get_by_id = AsyncMock(return_value=self.store)
        self.repository.delete = AsyncMock(return_value=None)
        self.service.files_service.delete_file = AsyncMock(  # type: ignore
            side_effect=FileNotFoundError
        )

        # When
        await self.service.delete_store("1", self.owner_id)  # type: ignore

        # Then
        self.repository.delete.assert_called_once_with("1")
        self.service.files_service.delete_file.assert_called_once_with("1")
