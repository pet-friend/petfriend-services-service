# mypy: disable-error-code="method-assign"
from uuid import uuid4

from sqlmodel import select
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.products import Product
from app.models.stores import Store
from app.repositories.products import ProductsRepository
from app.exceptions.repository import RecordNotFound
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from tests.tests_setup import BaseDbTestCase


class TestProductsRepository(BaseDbTestCase):
    # No need to mock the db - it's an in-memory sqlite db

    def setUp(self) -> None:
        super().setUp()
        self.store_create = StoreCreateFactory.build()
        self.store = Store(id=uuid4(), owner_id=uuid4(), **self.store_create.__dict__)
        self.product_create = ProductCreateFactory.build()
        self.product = Product(
            id=uuid4(), store_id=self.store.id, **self.product_create.model_dump()
        )
        self.product_repository = ProductsRepository(self.db)

    @pytest.mark.asyncio
    async def test_save_should_save_product_to_db(self) -> None:
        # Given
        self.db.add(self.store)
        await self.db.flush()

        # When
        saved_record = await self.product_repository.save(self.product)
        all_records = await self.product_repository.get_all()

        # Then
        assert all_records == [self.product]
        assert saved_record == self.product
        products = (await self.db.exec(select(Product))).all()
        assert len(products) == 1
        assert products[0] == self.product

    @pytest.mark.asyncio
    async def test_update_should_update_db(self) -> None:
        # Given
        self.db.add(self.store)
        await self.db.flush()

        product_2 = self.product.model_copy()
        product_2.description = ":D"
        created = await self.product_repository.save(self.product)

        # When
        updated = await self.product_repository.update(
            (created.store_id, created.id), product_2.model_dump()
        )
        all_records = await self.product_repository.get_all()

        # Then
        assert created == updated  # should update the original object

        assert updated.updated_at != product_2.updated_at  # should update the updated_at field
        product_2.updated_at = updated.updated_at

        assert updated == product_2
        assert all_records == [updated]

    @pytest.mark.asyncio
    async def test_delete_should_update_db(self) -> None:
        # Given
        self.db.add(self.store)
        await self.db.flush()

        saved_record = await self.product_repository.save(self.product)

        # When
        await self.product_repository.delete((saved_record.store_id, saved_record.id))
        all_records = await self.product_repository.get_all()

        # Then
        assert all_records == []
        products = (await self.db.exec(select(Product))).all()
        assert len(products) == 0

    @pytest.mark.asyncio
    async def test_update_raises_not_found(self) -> None:
        # Given setUp

        # When, Then
        with self.assertRaises(RecordNotFound):
            await self.product_repository.update(
                (self.product.store_id, self.product.id), self.product.model_dump()
            )

    @pytest.mark.asyncio
    async def test_delete_raises_not_found(self) -> None:
        # Given setUp

        # When, Then
        with self.assertRaises(RecordNotFound):
            await self.product_repository.delete((self.product.store_id, self.product.id))

    @pytest.mark.asyncio
    async def test_save_no_store_raises_integrity_error(self) -> None:
        # Given setUp

        # When, Then
        with pytest.raises(IntegrityError):
            await self.product_repository.save(self.product)

    @pytest.mark.asyncio
    async def test_save_get_by_name_should_return_if_exists(self) -> None:
        # Given
        self.db.add(self.store)
        await self.db.flush()
        self.db.add(self.product)
        await self.db.flush()

        # When
        saved_record = await self.product_repository.get_by_name(self.store.id, self.product.name)

        # Then
        assert saved_record == self.product

    @pytest.mark.asyncio
    async def test_save_get_by_name_should_return_if_not_exists(self) -> None:
        # Given
        self.db.add(self.store)
        await self.db.flush()
        self.db.add(self.product)
        await self.db.flush()

        # When
        saved_record = await self.product_repository.get_by_name(self.store.id, "random product")

        # Then
        assert saved_record is None
