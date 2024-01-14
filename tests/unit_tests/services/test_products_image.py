# mypy: disable-error-code="method-assign"
import datetime
from unittest.mock import AsyncMock, Mock
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

import pytest
from app.exceptions.products import ProductNotFound

from app.models.products import Product
from app.services.files import FilesService
from app.services.products import ProductsService
from app.repositories.products import ProductsRepository
from tests.factories.product_factories import ProductCreateFactory
from .util import File


class TestProductsService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.product_create = ProductCreateFactory.build()
        self.product = Product(
            id=uuid4(),
            created_at=datetime.datetime(2023, 1, 1),
            updated_at=datetime.datetime(2023, 1, 1),
            **self.product_create.__dict__,
        )

        self.repository = AsyncMock(spec=ProductsRepository)
        self.files_service = AsyncMock(spec=FilesService)
        self.service = ProductsService(self.repository, Mock(), self.files_service)
        self.file = File(open("tests/assets/test_image.jpg", "rb"))

    def tearDown(self) -> None:
        self.file.file.close()

    @pytest.mark.asyncio
    async def test_create_image_fail_if_product_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.create_product_image(
                self.product.store_id, self.product.id, self.file
            )

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))

    @pytest.mark.asyncio
    async def test_set_image_fail_if_product_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.set_product_image(self.product.store_id, self.product.id, self.file)

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))

    @pytest.mark.asyncio
    async def test_delete_image_fail_if_product_not_exists(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.delete_product_image(self.product.store_id, self.product.id)

        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))

    @pytest.mark.asyncio
    async def test_create_image_calls_create_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When
        await self.service.create_product_image(self.product.store_id, self.product.id, self.file)

        # Then
        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.create_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}", self.file
        )

    @pytest.mark.asyncio
    async def test_set_image_calls_set_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When
        await self.service.set_product_image(self.product.store_id, self.product.id, self.file)

        # Then
        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.set_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}", self.file
        )

    @pytest.mark.asyncio
    async def test_delete_image_calls_delete_file(self) -> None:
        # Given
        self.repository.get_by_id.return_value = self.product

        # When
        await self.service.delete_product_image(self.product.store_id, self.product.id)

        # Then
        self.repository.get_by_id.assert_called_once_with((self.product.store_id, self.product.id))
        self.files_service.delete_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}"
        )

    @pytest.mark.asyncio
    async def test_delete_product_deletes_image(self) -> None:
        # Given
        self.files_service.file_exists.return_value = True

        # When
        await self.service.delete_product(self.product.store_id, self.product.id)

        # Then
        self.files_service.file_exists.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}"
        )
        self.files_service.delete_file.assert_called_once_with(
            f"{self.product.store_id}-{self.product.id}"
        )
