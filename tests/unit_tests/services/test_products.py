from uuid import uuid4
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

import pytest
from app.exceptions.stores import StoreNotFound

from app.models.products import Product
from app.models.stores import Store
from app.services.products import ProductsService
from app.services.stores import StoresService
from app.services.files import FilesService
from app.repositories.products import ProductsRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.products import ProductNotFound, ProductAlreadyExists
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory


class TestProductsService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.product_create = ProductCreateFactory.build()

        self.store = Store(id=uuid4(), **StoreCreateFactory.build().model_dump())
        self.stores_service = AsyncMock(spec=StoresService)

        self.repository = AsyncMock(spec=ProductsRepository)
        self.files_service = AsyncMock(spec=FilesService)

        self.service = ProductsService(self.repository, self.stores_service, self.files_service)

    @pytest.mark.asyncio
    async def test_create_product_should_call_repository_save(self) -> None:
        # Given
        self.repository.get_by_name.return_value = None
        self.repository.save.side_effect = lambda x: x
        self.stores_service.get_store_by_id.return_value = self.store

        # When
        saved_record = await self.service.create_product(self.store.id, self.product_create)

        # Then
        assert self.product_create.model_dump().items() < saved_record.model_dump().items()
        self.repository.save.assert_called_once_with(saved_record)
        # should check if store exists
        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)

    @pytest.mark.asyncio
    async def test_create_product_fails_if_store_does_not_exist(self) -> None:
        # Given
        self.repository.get_by_id.return_value = None
        self.repository.save.side_effect = lambda x: x
        self.stores_service.get_store_by_id.side_effect = StoreNotFound()

        # When, Then
        with pytest.raises(StoreNotFound):
            await self.service.create_product(self.store.id, self.product_create)

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)

    @pytest.mark.asyncio
    async def test_get_product_should_call_repository_get_by_id(self) -> None:
        # Given
        product_id = uuid4()
        product = Product(store_id=self.store.id, id=product_id, **self.product_create.model_dump())
        self.repository.get_by_id.return_value = product

        # When
        saved_record = await self.service.get_product(self.store.id, product_id)

        # Then
        assert saved_record == product
        self.repository.get_by_id.assert_called_once_with((self.store.id, product_id))

    @pytest.mark.asyncio
    async def test_get_product_invalid_product_should_raise_exception(self) -> None:
        # Given
        self.repository.get_by_id.side_effect = ProductNotFound()

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.get_product(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_update_product_should_call_repository_update(self) -> None:
        # Given
        product_id = uuid4()
        product = Product(store_id=self.store.id, id=product_id, **self.product_create.model_dump())
        self.repository.update.side_effect = lambda _id, record: product

        # When
        saved_record = await self.service.update_product(
            self.store.id, product_id, self.product_create
        )

        # Then
        assert saved_record == product
        self.repository.update.assert_called_once_with(
            (self.store.id, product_id), self.product_create.model_dump()
        )

    @pytest.mark.asyncio
    async def test_delete_product_should_call_repository_delete(self) -> None:
        # Given
        product_id = uuid4()
        self.files_service.file_exists.return_value = False

        # When
        await self.service.delete_product(self.store.id, product_id)

        # Then
        self.repository.delete.assert_called_once_with((self.store.id, product_id))
        self.files_service.file_exists.assert_called_once_with(f"{self.store.id}-{product_id}")

    @pytest.mark.asyncio
    async def test_update_product_not_exists_should_raise(self) -> None:
        # Given
        product_id = uuid4()
        self.repository.update.side_effect = RecordNotFound()
        self.files_service.file_exists.return_value = False

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.update_product(self.store.id, product_id, self.product_create)

    @pytest.mark.asyncio
    async def test_delete_product_not_exists_should_raise(self) -> None:
        # Given
        product_id = uuid4()
        self.repository.delete.side_effect = RecordNotFound()

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.delete_product(self.store.id, product_id)

    @pytest.mark.asyncio
    async def test_create_product_already_exists_should_raise(self) -> None:
        # Given
        product = Product(store_id=self.store.id, id=uuid4(), **self.product_create.model_dump())
        self.repository.get_by_name.return_value = product

        # When, Then
        with self.assertRaises(ProductAlreadyExists):
            await self.service.create_product(self.store.id, self.product_create)

        self.repository.get_by_name.assert_called_once_with(self.store.id, self.product_create.name)
