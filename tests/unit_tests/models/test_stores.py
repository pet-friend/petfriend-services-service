from unittest import IsolatedAsyncioTestCase
from app.models.constants.stores import INVALID_DELIVERY_RANGE_MSG
from app.models.stores import StoreCreate
import pytest


class TestStoresModel(IsolatedAsyncioTestCase):
    @pytest.mark.asyncio
    async def test_store_create_validate_delivery_range(self) -> None:
        # Given
        delivery_range_km = -1
        # When
        with self.assertRaises(ValueError) as context:
            store_create = StoreCreate(
                name="test",
                description="test",
                delivery_range_km=delivery_range_km,
            )
            StoreCreate(**store_create.__dict__)

        # Then
        assert INVALID_DELIVERY_RANGE_MSG in str(context.exception)

    @pytest.mark.asyncio
    async def test_store_create_with_correct_delivery_range(self) -> None:
        # Given
        delivery_range_km = 5
        store_create = StoreCreate(
            name="test",
            description="test",
            delivery_range_km=delivery_range_km,
        )
        # When
        store_created = StoreCreate(**store_create.__dict__)

        # Then
        assert store_created.delivery_range_km == delivery_range_km
