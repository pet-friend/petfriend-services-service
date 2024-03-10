# mypy: disable-error-code="method-assign"
import datetime
from unittest.mock import AsyncMock
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

import pytest
from app.exceptions.stores import StoreNotFound

from app.models.stores import Store
from app.services.files import FilesService
from app.services.stores import StoresService
from app.repositories.stores import StoresRepository
from tests.factories.store_factories import StoreCreateFactory
from .util import File


class TestStoresService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.store_create = StoreCreateFactory.build(address=None)
        self.store = Store(
            id=uuid4(),
            owner_id=uuid4(),
            created_at=datetime.datetime(2023, 1, 1),
            updated_at=datetime.datetime(2023, 1, 1),
            **self.store_create.__dict__
        )

        self.repository = AsyncMock(spec=StoresRepository)
        self.files_service = AsyncMock(spec=FilesService)
        self.service = StoresService(self.repository, self.files_service)
        self.file = File(open("tests/assets/test_image.jpg", "rb"))

    def tearDown(self) -> None:
        self.file.file.close()

    @pytest.mark.asyncio
    async def test_create_image_fail_if_store_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(StoreNotFound):
            await self.service.create_store_image(self.store.id, self.file)

        self.repository.get_by_id.assert_called_once_with(self.store.id)

    @pytest.mark.asyncio
    async def test_set_image_fail_if_store_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(StoreNotFound):
            await self.service.set_store_image(self.store.id, self.file)

        self.repository.get_by_id.assert_called_once_with(self.store.id)

    @pytest.mark.asyncio
    async def test_delete_image_fail_if_store_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(StoreNotFound):
            await self.service.delete_store_image(self.store.id)

        self.repository.get_by_id.assert_called_once_with(self.store.id)

    @pytest.mark.asyncio
    async def test_create_image_calls_create_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When
        await self.service.create_store_image(self.store.id, self.file)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.create_file.assert_called_once_with(self.store.id, self.file)

    @pytest.mark.asyncio
    async def test_set_image_calls_set_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When
        await self.service.set_store_image(self.store.id, self.file)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.set_file.assert_called_once_with(self.store.id, self.file)

    @pytest.mark.asyncio
    async def test_delete_image_calls_delete_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.store

        # When
        await self.service.delete_store_image(self.store.id)

        # Then
        self.repository.get_by_id.assert_called_once_with(self.store.id)
        self.files_service.delete_file.assert_called_once_with(self.store.id)
