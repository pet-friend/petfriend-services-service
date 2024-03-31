from unittest import IsolatedAsyncioTestCase
from app.models.constants.stores import INVALID_DELIVERY_RANGE_MSG, INVALID_SHIPPING_COST_MSG
from app.models.stores import StoreCreate


class TestStoresModel(IsolatedAsyncioTestCase):
    async def test_store_create_validate_delivery_range(self) -> None:
        # Given
        delivery_range_km = -1
        # When
        with self.assertRaises(ValueError) as context:
            store_create = StoreCreate(
                name="test",
                description="test",
                delivery_range_km=delivery_range_km,
                shipping_cost=5,
            )
            StoreCreate(**store_create.__dict__)

        # Then
        assert INVALID_DELIVERY_RANGE_MSG in str(context.exception)

    async def test_store_create_with_correct_delivery_range(self) -> None:
        # Given
        delivery_range_km = 5
        store_create = StoreCreate(
            name="test",
            description="test",
            delivery_range_km=delivery_range_km,
            shipping_cost=5,
        )
        # When
        store_created = StoreCreate(**store_create.__dict__)

        # Then
        assert store_created.delivery_range_km == delivery_range_km

    async def test_store_create_validate_shipping_cost(self) -> None:
        # Given
        shipping_cost = -1
        # When
        with self.assertRaises(ValueError) as context:
            store_create = StoreCreate(
                name="test",
                description="test",
                delivery_range_km=5,
                shipping_cost=shipping_cost,
            )
            StoreCreate(**store_create.__dict__)

        # Then
        assert INVALID_SHIPPING_COST_MSG in str(context.exception)

    async def test_store_create_with_correct_shipping_cost(self) -> None:
        # Given
        shipping_cost = 5
        store_create = StoreCreate(
            name="test",
            description="test",
            delivery_range_km=5,
            shipping_cost=shipping_cost,
        )
        # When
        store_created = StoreCreate(**store_create.__dict__)

        # Then
        assert store_created.shipping_cost == shipping_cost
