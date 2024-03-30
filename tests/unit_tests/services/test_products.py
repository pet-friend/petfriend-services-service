from uuid import uuid4
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
import pytest
from app.exceptions.stores import StoreNotFound
from app.exceptions.users import Forbidden

from app.models.products import Category, Product, ProductCreate
from app.models.stores import Store
from app.services.products import ProductsService
from app.services.stores import StoresService
from app.services.files import FilesService
from app.repositories.products import ProductsRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.products import ProductNotFound, ProductAlreadyExists, ProductOutOfStock
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory


class TestProductsService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.product_create = ProductCreateFactory.build()
        self.owner_id = uuid4()
        self.store = Store(
            id=uuid4(),
            owner_id=self.owner_id,
            **StoreCreateFactory.build(address=None).model_dump(),
        )
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
        saved_record = await self.service.create_product(
            self.store.id, self.product_create, self.owner_id
        )
        saved_record = Product(**saved_record.model_dump())
        # Then
        assert len(self.product_create.model_dump().items()) <= len(
            saved_record.model_dump().items()
        )
        self.repository.save.assert_called_once()
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
            await self.service.create_product(self.store.id, self.product_create, self.owner_id)

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)

    @pytest.mark.asyncio
    async def test_create_product_fails_if_not_the_owner(self) -> None:
        # Given
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.create_product(self.store.id, self.product_create, uuid4())

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)
        self.repository.save.assert_not_called()

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
    async def test_delete_product_should_call_repository_delete(self) -> None:
        # Given
        product_id = uuid4()
        self.files_service.file_exists.return_value = False
        self.stores_service.get_store_by_id.return_value = self.store

        # When
        await self.service.delete_product(self.store.id, product_id, self.owner_id)

        # Then
        self.repository.delete.assert_called_once_with((self.store.id, product_id))
        self.files_service.file_exists.assert_called_once_with(f"{self.store.id}-{product_id}")

    @pytest.mark.asyncio
    async def test_update_product_not_exists_should_raise(self) -> None:
        # Given
        product_id = uuid4()
        self.repository.update.side_effect = RecordNotFound()
        self.files_service.file_exists.return_value = False
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.update_product(
                self.store.id, product_id, self.product_create, self.owner_id
            )

    @pytest.mark.asyncio
    async def test_update_product_fails_if_not_the_owner(self) -> None:
        # Given
        product_id = uuid4()
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with self.assertRaises(Forbidden):
            await self.service.update_product(
                self.store.id, product_id, self.product_create, uuid4()
            )

        self.repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_product_not_exists_should_raise(self) -> None:
        # Given
        product_id = uuid4()
        self.repository.delete.side_effect = RecordNotFound()
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with self.assertRaises(ProductNotFound):
            await self.service.delete_product(self.store.id, product_id, self.owner_id)

    @pytest.mark.asyncio
    async def test_delete_product_fails_if_not_the_owner(self) -> None:
        # Given
        product_id = uuid4()
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with self.assertRaises(Forbidden):
            await self.service.delete_product(self.store.id, product_id, uuid4())

        self.repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_product_already_exists_should_raise(self) -> None:
        # Given
        product = Product(store_id=self.store.id, id=uuid4(), **self.product_create.model_dump())
        self.repository.get_by_name.return_value = product
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with self.assertRaises(ProductAlreadyExists):
            await self.service.create_product(self.store.id, self.product_create, self.owner_id)

        self.repository.get_by_name.assert_called_once_with(self.store.id, self.product_create.name)

    @pytest.mark.asyncio
    async def test_create_product_should_call_repo_save_with_ProductCategories(self) -> None:
        # Given
        self.repository.get_by_name.return_value = None
        self.repository.save.side_effect = lambda x: x
        self.stores_service.get_store_by_id.return_value = self.store

        # When
        await self.service.create_product(self.store.id, self.product_create, self.owner_id)

        # Then
        self.repository.save.assert_called_once()
        save_args = self.repository.save.call_args.args[0]
        for i in range(len(self.product_create.categories)):
            assert save_args._categories[i].category == self.product_create.categories[i]

    @pytest.mark.asyncio
    async def test_update_product_should_call_repo_update_with_ProductCategories(self) -> None:
        # Given
        self.repository.get_by_name.return_value = None
        self.repository.save.side_effect = lambda x: x
        self.stores_service.get_store_by_id.return_value = self.store

        # When
        await self.service.create_product(self.store.id, self.product_create, self.owner_id)
        new_categories = [Category("alimentos")]
        save_args = self.repository.save.call_args.args[0]
        product_copy = ProductCreate(**save_args.model_dump() | {"categories": new_categories})
        await self.service.update_product(self.store.id, save_args.id, product_copy, self.owner_id)

        # Then
        self.repository.update.assert_called_once()
        update_args = self.repository.update.call_args.args[1]
        for i in range(len(new_categories)):
            assert update_args["_categories"][i].category == new_categories[i]

    @pytest.mark.asyncio
    async def test_update_stock_should_call_repo_save(self) -> None:
        # Given
        product = Product(
            store_id=self.store.id,
            id=uuid4(),
            **{**self.product_create.model_dump(), "available": 3},
        )

        # When
        await self.service.update_stock(product, 5)

        # Then
        assert product.available == 8
        self.repository.save.assert_called_once_with(product)

    @pytest.mark.asyncio
    async def test_update_stock_should_not_call_repo_save_if_not_specified(self) -> None:
        # Given
        product = Product(
            store_id=self.store.id,
            id=uuid4(),
            **{**self.product_create.model_dump(), "available": None},
        )

        # When
        await self.service.update_stock(product, 5)

        # Then
        assert product.available is None
        self.repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_stock_should_raise_if_not_enough(self) -> None:
        # Given
        product = Product(
            store_id=self.store.id,
            id=uuid4(),
            **{**self.product_create.model_dump(), "available": 4},
        )

        # When, Then
        with pytest.raises(ProductOutOfStock):
            await self.service.update_stock(product, -5)

        self.repository.save.assert_not_called()
