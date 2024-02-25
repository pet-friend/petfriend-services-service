# mypy: disable-error-code="method-assign"
import datetime
from uuid import uuid4
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy import ScalarResult
import pytest

from app.models.service import Service, ServiceType
from app.models.stores import Store
from app.repositories.stores import StoresRepository
from tests.factories.store_factories import StoreCreateFactory


class TestStoresRepository(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.store_create = StoreCreateFactory.build()
        service = Service(id=uuid4(), type=ServiceType.STORE)
        self.store = Store(
            service=service,
            owner_id=uuid4(),
            created_at=datetime.datetime(2023, 1, 1),
            updated_at=datetime.datetime(2023, 1, 1),
            **self.store_create.__dict__
        )

        self.async_session = AsyncMock()
        self.stores_repository = StoresRepository(self.async_session)

    @pytest.mark.asyncio
    async def test_save_should_save_store_to_db(self) -> None:
        # Given
        self.stores_repository.save = AsyncMock(return_value=self.store)

        with patch("app.repositories.stores.Store") as store_cls_mock, patch(
            "app.repositories.stores.Service"
        ) as service_cls_mock:
            store_cls_mock.return_value = self.store
            service_cls_mock.return_value = self.store.service

            # When
            saved_record = await self.stores_repository.create(
                self.store_create, self.store.owner_id
            )

            # Then
            assert saved_record == self.store
            store_cls_mock.assert_called_once_with(
                **self.store_create.__dict__,
                owner_id=self.store.owner_id,
                service=self.store.service
            )
            service_cls_mock.assert_called_once_with(type=ServiceType.STORE)
            self.stores_repository.save.assert_called_once_with(self.store)

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_count_all_should_return_count_of_stores(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=1)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all()

        # Then
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_all_should_return_count_of_stores_with_filters(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=1)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all(name="test")

        # Then
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_all_should_return_zero_if_no_stores(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=0)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all()

        # Then
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_all_should_return_zero_if_no_stores_with_filters(self) -> None:
        # Given
        result: ScalarResult[int] = AsyncMock()
        result.one = Mock(return_value=0)
        self.async_session.exec = AsyncMock(return_value=result)

        # When
        count = await self.stores_repository.count_all(name="test")

        # Then
        assert count == 0
