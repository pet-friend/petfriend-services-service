# mypy: disable-error-code="method-assign"
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from sqlalchemy import ScalarResult

from app.models.addresses import Address
from app.models.stores import Store
from app.repositories.stores import StoresRepository
from tests.factories.store_factories import StoreCreateFactory


class TestStoresRepository:
    def setup_method(self) -> None:
        self.store_create = StoreCreateFactory.build()
        self.store = Store(
            owner_id=uuid4(),
            address=Address(latitude=0, longitude=0, **self.store_create.address.model_dump()),
            **self.store_create.model_dump(exclude={"address"})
        )
        self.async_session = AsyncMock()
        self.stores_repository = StoresRepository(self.async_session)

    async def test_get_by_name_should_get_store_by_name(self) -> None:
        # Given
        name = self.store_create.name
        result: ScalarResult[Store] = AsyncMock()
        result.all = Mock(return_value=[self.store])
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        fetched_record = await self.stores_repository.get_by_name(name)

        # Then
        assert fetched_record == self.store

    async def test_get_by_name_should_return_none_if_store_does_not_exist(self) -> None:
        # Given
        name = self.store_create.name
        result: ScalarResult[Store] = AsyncMock()
        result.all = Mock(return_value=[])
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        fetched_record = await self.stores_repository.get_by_name(name)

        # Then
        assert fetched_record is None

    async def test_count_all_should_return_count_of_stores(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=1)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all()

        # Then
        assert count == 1

    async def test_count_all_should_return_count_of_stores_with_filters(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=1)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all(name="test")

        # Then
        assert count == 1

    async def test_count_all_should_return_zero_if_no_stores(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=0)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all()

        # Then
        assert count == 0

    async def test_count_all_should_return_zero_if_no_stores_with_filters(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=0)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all(name="test")

        # Then
        assert count == 0
