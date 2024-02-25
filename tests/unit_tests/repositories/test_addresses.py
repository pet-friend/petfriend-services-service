# mypy: disable-error-code="method-assign"
import datetime
from uuid import uuid4

from sqlmodel import select
import pytest
from pydantic_extra_types.country import CountryAlpha2

from app.models.addresses import Address
from app.models.service import Service, ServiceType
from app.repositories.addresses import AddressesRepository
from app.exceptions.repository import RecordNotFound
from tests.factories.address_factories import AddressCreateFactory
from tests.tests_setup import BaseDbTestCase


class TestAddressesRepository(BaseDbTestCase):
    # No need to mock the db - it's an in-memory sqlite db

    def setUp(self) -> None:
        super().setUp()

        self.service = Service(id=uuid4(), type=ServiceType.STORE)
        self.address_create = AddressCreateFactory.build(type="other", country_code="AR")
        self.address = Address(
            id=self.service.id,
            created_at=datetime.datetime(2023, 1, 1),
            updated_at=datetime.datetime(2023, 1, 1),
            latitude=-34.6036844,
            longitude=-58.3815591,
            **self.address_create.model_dump()
        )
        self.address_repository = AddressesRepository(self.db)

    @pytest.mark.asyncio
    async def test_save_should_save_address_to_db(self) -> None:
        # Given
        self.db.add(self.service)
        await self.db.flush()

        # When
        saved_record = await self.address_repository.save(self.address)
        all_records = await self.address_repository.get_all()

        # Then
        assert all_records == [self.address]
        assert saved_record == self.address
        addresses = (await self.db.exec(select(Address))).all()
        assert len(addresses) == 1
        assert addresses[0] == self.address

    @pytest.mark.asyncio
    async def test_update_should_update_db(self) -> None:
        # Given
        self.db.add(self.service)
        await self.db.flush()
        address_2 = self.address.model_copy()
        address_2.country_code = CountryAlpha2("BR")
        created = await self.address_repository.save(self.address)

        # When
        updated = await self.address_repository.update(created.id, address_2.model_dump())
        all_records = await self.address_repository.get_all()

        # Then
        assert created == updated  # should update the original object

        assert updated.updated_at != address_2.updated_at  # should update the updated_at field
        address_2.updated_at = updated.updated_at

        assert updated.model_dump() == address_2.model_dump()
        assert all_records == [updated]

    @pytest.mark.asyncio
    async def test_delete_should_update_db(self) -> None:
        # Given
        self.db.add(self.service)
        await self.db.flush()

        # When
        saved_record = await self.address_repository.save(self.address)
        await self.address_repository.delete(saved_record.id)
        all_records = await self.address_repository.get_all()

        # Then
        assert all_records == []
        addresses = (await self.db.exec(select(Address))).all()
        assert len(addresses) == 0

    @pytest.mark.asyncio
    async def test_update_raises_not_found(self) -> None:
        # Given setUp

        # When, Then
        with self.assertRaises(RecordNotFound):
            await self.address_repository.update(self.address.id, self.address.model_dump())

    @pytest.mark.asyncio
    async def test_delete_raises_not_found(self) -> None:
        # Given setUp

        # When, Then
        with self.assertRaises(RecordNotFound):
            await self.address_repository.delete(self.address.id)
