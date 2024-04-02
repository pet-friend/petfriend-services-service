# mypy: disable-error-code="method-assign"
from uuid import uuid4

from sqlmodel import select
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.addresses import Address
from app.models.stores import Store, Product
from app.repositories.stores import ProductsRepository
from app.exceptions.repository import RecordNotFound
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from tests.tests_setup import BaseDbTestCase


class TestProductsRepository(BaseDbTestCase):
    # No need to mock the db - it's an in-memory sqlite db

    @pytest.fixture(autouse=True)
    def setup(self, setup_db: None) -> None:
        self.store_create = StoreCreateFactory.build()
        self.store = Store(
            owner_id=uuid4(),
            address=Address(latitude=0, longitude=0, **self.store_create.address.model_dump()),
            **self.store_create.model_dump(exclude={"address"}),
        )
        self.product_create = ProductCreateFactory.build()
        self.product = Product(
            id=uuid4(), store_id=self.store.id, **self.product_create.model_dump()
        )
        self.product_repository = ProductsRepository(self.db)

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

    async def test_update_should_update_db(self) -> None:
        # Given
        self.db.add(self.store)
        await self.db.flush()

        created = await self.product_repository.save(self.product)
        created_copy = created.model_copy()
        created_copy.description = ":D"

        # When
        updated = await self.product_repository.update(
            (created.store_id, created.id), created_copy.model_dump()
        )
        all_records = await self.product_repository.get_all()

        # Then
        assert created.id == updated.id

        assert created_copy.created_at == updated.created_at
        assert created_copy.updated_at != updated.updated_at

        created_copy.updated_at = updated.updated_at
        assert created_copy.model_dump() == updated.model_dump()
        assert all_records == [updated]

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

    async def test_update_raises_not_found(self) -> None:
        # Given setUp

        # When, Then
        with pytest.raises(RecordNotFound):
            await self.product_repository.update(
                (self.product.store_id, self.product.id), self.product.model_dump()
            )

    async def test_delete_raises_not_found(self) -> None:
        # Given setUp

        # When, Then
        with pytest.raises(RecordNotFound):
            await self.product_repository.delete((self.product.store_id, self.product.id))

    async def test_save_no_store_raises_integrity_error(self) -> None:
        # Given setUp

        # When, Then
        with pytest.raises(IntegrityError):
            await self.product_repository.save(self.product)

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
