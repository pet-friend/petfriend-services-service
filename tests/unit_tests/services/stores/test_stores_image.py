# mypy: disable-error-code="method-assign"
from unittest.mock import AsyncMock
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

import pytest

from app.exceptions.stores import StoreNotFound
from app.exceptions.users import Forbidden
from app.models.addresses import Address
from app.models.stores import Store
from app.services.files import FilesService
from app.services.stores import StoresService
from app.repositories.stores import StoresRepository
from tests.factories.store_factories import StoreCreateFactory
from ..util import File


@pytest.mark.usefixtures("blob_setup")
class TestStoresService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.store_create = StoreCreateFactory.build()
        self.owner_id = uuid4()

        self.store = Store(
            owner_id=self.owner_id,
            address=Address(latitude=0, longitude=0, **self.store_create.address.model_dump()),
            **self.store_create.model_dump(exclude={"address"})
        )

        self.repository = AsyncMock(spec=StoresRepository)
        self.files_service = AsyncMock(spec=FilesService)
        self.service = StoresService(self.repository, self.files_service)
        self.file = File(open("tests/assets/test_image.jpg", "rb"))

    def tearDown(self) -> None:
        self.file.file.close()

    async def test_create_image_fail_if_store_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(StoreNotFound):
            await self.service.create_store_image(self.store.id, self.file, self.owner_id)

        self.repository.get_by_id.assert_called_once_with(self.store.id)

    async def test_set_image_fail_if_store_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(StoreNotFound):
            await self.service.set_store_image(self.store.id, self.file, self.owner_id)

        self.repository.get_by_id.assert_called_once_with(self.store.id)

    async def test_delete_image_fail_if_store_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(StoreNotFound):
            await self.service.delete_store_image(self.store.id, self.owner_id)

        self.repository.get_by_id.assert_called_once_with(self.store.id)

    async def test_create_image_calls_create_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When
        await self.service.create_store_image(self.store.id, self.file, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.create_file.assert_called_once_with(self.store.id, self.file)

    async def test_cant_create_image_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.create_store_image(self.store.id, self.file, uuid4())

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.create_file.assert_not_called()

    async def test_set_image_calls_set_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When
        await self.service.set_store_image(self.store.id, self.file, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.set_file.assert_called_once_with(self.store.id, self.file)

    async def test_cant_set_image_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.set_store_image(self.store.id, self.file, uuid4())

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.set_file.assert_not_called()

    async def test_delete_image_calls_delete_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When
        await self.service.delete_store_image(self.store.id, self.owner_id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.delete_file.assert_called_once_with(self.store.id)

    async def test_cant_delete_image_if_not_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.delete_store_image(self.store.id, uuid4())

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.delete_file.assert_not_called()
