# mypy: disable-error-code="method-assign"
import datetime
from unittest.mock import AsyncMock
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

import pytest
from app.exceptions.products import ProductNotFound
from app.exceptions.users import Forbidden

from app.models.products import Product
from app.models.stores import Store
from app.services.files import FilesService
from app.services.products import ProductsService
from app.repositories.products import ProductsRepository
from app.services.stores import StoresService
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from .util import File


class TestProductsService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.owner_id = uuid4()
        self.store = Store(
            id=uuid4(),
            owner_id=self.owner_id,
            **StoreCreateFactory.build(address=None).model_dump(),
        )
        self.stores_service = AsyncMock(spec=StoresService)
        self.product_create = ProductCreateFactory.build()
        self.product = Product(
            id=uuid4(),
            store_id=self.store.id,
            store=self.store,
            created_at=datetime.datetime(2023, 1, 1),
            updated_at=datetime.datetime(2023, 1, 1),
            **self.product_create.__dict__,
        )
        self.repository = AsyncMock(spec=ProductsRepository)
        self.files_service = AsyncMock(spec=FilesService)
        self.service = ProductsService(self.repository, self.stores_service, self.files_service)
        self.file = File(open("tests/assets/test_image.jpg", "rb"))

    def tearDown(self) -> None:
        self.file.file.close()

    async def test_create_image_fail_if_product_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.create_product_image(
                self.product.store_id, self.product.id, self.file, self.owner_id
            )

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))

    async def test_set_image_fail_if_product_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.set_product_image(
                self.product.store_id, self.product.id, self.file, self.owner_id
            )

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))

    async def test_delete_image_fail_if_product_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.delete_product_image(
                self.product.store_id, self.product.id, self.owner_id
            )

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))

    async def test_delete_image_fail_if_not_store_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When, Then
        with self.assertRaises(Forbidden):
            await self.service.delete_product_image(self.product.store_id, self.product.id, uuid4())

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.delete_file.assert_not_called()

    async def test_create_image_fail_if_not_store_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When, Then
        with self.assertRaises(Forbidden):
            await self.service.create_product_image(
                self.product.store_id, self.product.id, self.file, uuid4()
            )

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.create_file.assert_not_called()

    async def test_update_image_fail_if_not_store_owner(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When, Then
        with self.assertRaises(Forbidden):
            await self.service.set_product_image(
                self.product.store_id, self.product.id, self.file, uuid4()
            )

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.set_file.assert_not_called()

    async def test_create_image_calls_create_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When
        url = await self.service.create_product_image(
            self.product.store_id, self.product.id, self.file, self.owner_id
        )

        # Then
        assert url
        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.create_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}", self.file
        )

    async def test_set_image_calls_set_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When
        url = await self.service.set_product_image(
            self.product.store_id, self.product.id, self.file, self.owner_id
        )

        # Then
        assert url
        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.set_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}", self.file
        )

    async def test_delete_image_calls_delete_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When
        await self.service.delete_product_image(
            self.product.store_id, self.product.id, self.owner_id
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.delete_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}"
        )

    async def test_delete_product_deletes_image(self) -> None:
        # Given
        self.files_service.file_exists.return_value = True
        self.stores_service.get_store_by_id.return_value = self.store

        # When
        await self.service.delete_product(self.product.store_id, self.product.id, self.owner_id)

        # Then
        self.files_service.file_exists.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}"
        )
        self.files_service.delete_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}"
        )
