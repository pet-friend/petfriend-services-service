from decimal import Decimal
from typing import Any
from uuid import uuid4
from unittest.mock import AsyncMock, call

from httpx import URL
import pytest
from pytest_httpx import HTTPXMock

from app.exceptions.products import ProductNotFound, ProductOutOfStock
from app.exceptions.users import Forbidden
from app.exceptions.purchases import (
    CantPurchaseFromOwnStore,
    OutsideDeliveryRange,
    PurchaseNotFound,
    StoreNotReady,
)

from app.models.addresses import Address
from app.models.preferences import PurchaseTypes
from app.models.stores import Store, Purchase, PurchaseItem, PurchaseStatus, Product, ProductRead
from app.models.util import Coordinates, Id
from app.repositories.stores import PurchasesRepository
from app.services.stores import ProductsService, PurchasesService
from app.services.stores import StoresService
from app.services.users import UsersService
from app.config import settings

from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from tests.util import CustomMatcher


class TestPurchasesService:
    def setup_method(self) -> None:
        self.owner_id = uuid4()

        store_create = StoreCreateFactory.build()
        self.store = Store(
            owner_id=self.owner_id,
            address=Address(latitude=0, longitude=0, **store_create.address.model_dump()),
            **store_create.model_dump(exclude={"address"}),
        )

        self.product = Product(
            id=uuid4(),
            store_id=self.store.id,
            store=self.store,
            **ProductCreateFactory.build().model_dump(),
        )
        self.store.products = [self.product]

        self.stores_service = AsyncMock(spec=StoresService)
        self.products_service = AsyncMock(spec=ProductsService)
        self.repository = AsyncMock(spec=PurchasesRepository)
        self.users_service = AsyncMock(spec=UsersService)

        self.service = PurchasesService(
            self.stores_service, self.products_service, self.users_service, self.repository
        )

    async def test_get_purchase_by_store_owner_should_call_repository_get_by_id(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        saved_record = await self.service.get_purchase(
            self.store.id, purchase_id, self.store.owner_id
        )

        # Then
        assert saved_record == purchase
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))

    async def test_get_purchase_by_buyer_should_call_repository_get_by_id(self) -> None:
        # Given
        purchase_id = uuid4()
        buyer = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=buyer,
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        saved_record = await self.service.get_purchase(self.store.id, purchase_id, buyer)

        # Then
        assert saved_record == purchase
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))

    async def test_get_purchase_unrelated_user_should_raise(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.get_purchase(self.store.id, purchase_id, uuid4())

        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))

    async def test_get_purchase_not_exists_should_raise(self) -> None:
        # Given
        purchase_id = uuid4()
        self.repository.get_by_id.return_value = None

        # When, Then
        with pytest.raises(PurchaseNotFound):
            await self.service.get_purchase(self.store.id, purchase_id, uuid4())

        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))

    async def test_get_store_purchases_unrelated_user_should_raise(self) -> None:
        # Given
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.get_store_purchases(self.store.id, uuid4(), 5, 5)

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)

    async def test_get_store_purchases_store_owner_user_should_return(self) -> None:
        # Given
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=uuid4(),
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.stores_service.get_store_by_id.return_value = self.store
        self.repository.get_all.return_value = [purchase]
        self.repository.count_all.return_value = 1

        # When
        purchases, total = await self.service.get_store_purchases(
            self.store.id, self.store.owner_id, 5, 0
        )

        # Then
        assert total == 1
        assert purchases[0] == purchase
        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)
        self.repository.get_all.assert_called_once_with(store_id=self.store.id, limit=5, skip=0)
        self.repository.count_all.assert_called_once_with(store_id=self.store.id)

    async def test_purchase_no_products_should_raise(self) -> None:
        # Given
        quantities: dict[Id, int] = {}

        # When, Then
        with pytest.raises(ProductNotFound):
            await self.service.purchase(self.store.id, quantities, uuid4(), uuid4(), "token")

    async def test_purchase_from_self_should_raise(self) -> None:
        # Given
        self.stores_service.get_store_by_id.return_value = self.store

        # When, Then
        with pytest.raises(CantPurchaseFromOwnStore):
            await self.service.purchase(
                self.store.id, {uuid4(): 1}, self.store.owner_id, uuid4(), "token"
            )

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)

    async def test_purchase_too_far_should_raise(self) -> None:
        # Given
        self.stores_service.get_store_by_id.return_value = self.store
        self.products_service.get_products_read.return_value = [
            ProductRead(categories=[], **self.product.model_dump())
        ]
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=50, longitude=50
        )
        user_id = uuid4()
        user_address_id = uuid4()

        # When, Then
        with pytest.raises(OutsideDeliveryRange):
            await self.service.purchase(
                self.store.id, {self.product.id: 1}, user_id, user_address_id, "token"
            )

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)
        self.users_service.get_user_address_coordinates.assert_called_once_with(
            user_id, user_address_id, "token"
        )

    async def test_purchase_no_stock_should_raise(self) -> None:
        # Given
        self.product.available = 2
        self.stores_service.get_store_by_id.return_value = self.store
        self.products_service.get_products_read.return_value = [
            ProductRead(categories=[], **self.product.model_dump())
        ]
        self.products_service.update_stock.side_effect = ProductOutOfStock
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=0, longitude=0
        )
        user_id = uuid4()
        user_address_id = uuid4()
        quantities = {self.product.id: 3}

        # When, Then
        with pytest.raises(ProductOutOfStock):
            await self.service.purchase(
                self.store.id, quantities, user_id, user_address_id, "token"
            )

        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)
        self.users_service.get_user_address_coordinates.assert_called_once_with(
            user_id, user_address_id, "token"
        )
        self.products_service.update_stock.assert_called_once_with(
            self.product, -1 * quantities[self.product.id]
        )

    async def test_purchase_one_item(self, httpx_mock: HTTPXMock) -> None:
        # Given
        self.product.available = 2
        self.stores_service.get_store_by_id.return_value = self.store
        image_url = "http://image.url"
        self.products_service.get_products_read.return_value = [
            ProductRead(categories=[], image_url=image_url, **self.product.model_dump())
        ]
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=0, longitude=0
        )
        user_id = uuid4()
        user_address_id = uuid4()
        quantities = {self.product.id: 3}
        self.product.percent_off = Decimal(10)

        token = "token"
        result_url = "result url"
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(self.store.owner_id),
            },
        )

        service_reference: str
        unit_price = self.product.price * (100 - self.product.percent_off) / 100
        fee = unit_price * quantities[self.product.id] * settings.FEE_PERCENTAGE / 100

        def check_request_body(data: dict[str, Any]) -> None:
            nonlocal service_reference
            service_reference = data["service_reference"]
            pref_data = data["preference_data"]

            assert data["type"] == PurchaseTypes.STORE_PURCHASE
            assert len(pref_data["items"]) == 1
            assert pref_data["items"][0] == {
                "title": self.product.name,
                "description": self.product.description,
                "currency_id": "ARS",
                "quantity": quantities[self.product.id],
                "unit_price": float(unit_price),
                "picture_url": image_url,
            }
            assert pref_data["marketplace_fee"] == float(fee)
            assert pref_data["shipments"] == {
                "cost": float(self.store.shipping_cost),
                "mode": "not_specified",
            }
            assert pref_data["metadata"] == {
                "store_id": str(self.store.id),
                "purchase_id": service_reference,
                "type": PurchaseTypes.STORE_PURCHASE,
            }

        httpx_mock.add_response(
            url=url,
            match_json=CustomMatcher(check_request_body),
            headers={"Authorization": f"Bearer {token}"},
            json=result_url,
        )

        # When
        purchase = await self.service.purchase(
            self.store.id, quantities, user_id, user_address_id, "token"
        )

        # Then
        self.stores_service.get_store_by_id.assert_called_once_with(self.store.id)
        self.users_service.get_user_address_coordinates.assert_called_once_with(
            user_id, user_address_id, "token"
        )
        self.products_service.update_stock.assert_called_once_with(
            self.product, -1 * quantities[self.product.id]
        )
        assert purchase.status == PurchaseStatus.CREATED
        assert purchase.payment_url == result_url
        assert str(purchase.id) == service_reference
        assert purchase.store == self.store
        assert purchase.buyer_id == user_id
        assert len(purchase.items) == 1
        assert purchase.items[0].product_id == self.product.id
        assert purchase.items[0].quantity == quantities[self.product.id]
        assert purchase.items[0].unit_price == unit_price

    async def test_purchase_store_payment_not_linked(self, httpx_mock: HTTPXMock) -> None:
        # Given
        self.product.available = 2
        self.stores_service.get_store_by_id.return_value = self.store
        image_url = "http://image.url"
        self.products_service.get_products_read.return_value = [
            ProductRead(categories=[], image_url=image_url, **self.product.model_dump())
        ]
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=0, longitude=0
        )
        quantities = {self.product.id: 3}

        token = "token"
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(self.store.owner_id),
            },
        )
        httpx_mock.add_response(
            url=url, headers={"Authorization": f"Bearer {token}"}, status_code=404
        )

        # When, Then
        with pytest.raises(StoreNotReady):
            await self.service.purchase(self.store.id, quantities, uuid4(), uuid4(), "token")

    async def test_cant_update_completed_purchase(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.COMPLETED,
            payment_url=None,
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_purchase_status(
                self.store.id, purchase_id, PurchaseStatus.IN_PROGRESS
            )

        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        self.repository.save.assert_not_called()
        self.products_service.update_stock.assert_not_called()

    async def test_cant_update_cancelled_purchase(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CANCELLED,
            payment_url=None,
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_purchase_status(
                self.store.id, purchase_id, PurchaseStatus.IN_PROGRESS
            )

        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        self.repository.save.assert_not_called()
        self.products_service.update_stock.assert_not_called()

    async def test_update_purchase_cancelled_idempotent(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CANCELLED,
            payment_url=None,
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        await self.service.update_purchase_status(
            self.store.id, purchase_id, PurchaseStatus.CANCELLED
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        self.repository.save.assert_not_called()
        self.products_service.update_stock.assert_not_called()

    async def test_update_purchase_completed_idempotent(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.COMPLETED,
            payment_url=None,
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        await self.service.update_purchase_status(
            self.store.id, purchase_id, PurchaseStatus.COMPLETED
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        self.repository.save.assert_not_called()
        self.products_service.update_stock.assert_not_called()

    async def test_update_purchase_completed(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), quantity=1, unit_price=10),  # type: ignore
            PurchaseItem(product_id=uuid4(), quantity=2, unit_price=20),  # type: ignore
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        await self.service.update_purchase_status(
            self.store.id, purchase_id, PurchaseStatus.COMPLETED
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        purchase.status = PurchaseStatus.COMPLETED
        purchase.payment_url = None  # type: ignore
        self.repository.save.assert_called_once_with(purchase)
        self.products_service.update_stock.assert_not_called()

    async def test_update_purchase_cancelled(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), product=AsyncMock(), quantity=5, unit_price=10),  # type: ignore # noqa
            PurchaseItem(product_id=uuid4(), product=AsyncMock(), quantity=2, unit_price=20),  # type: ignore # noqa
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        await self.service.update_purchase_status(
            self.store.id, purchase_id, PurchaseStatus.CANCELLED
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        purchase.status = PurchaseStatus.CANCELLED
        purchase.payment_url = None  # type: ignore
        self.repository.save.assert_called_once_with(purchase)
        stock_calls = [call(item.product, item.quantity) for item in items]
        self.products_service.update_stock.assert_has_calls(stock_calls)

    async def test_update_purchase_in_progress(self) -> None:
        # Given
        purchase_id = uuid4()
        items = [
            PurchaseItem(product_id=uuid4(), product=AsyncMock(), quantity=5, unit_price=10),  # type: ignore # noqa
            PurchaseItem(product_id=uuid4(), product=AsyncMock(), quantity=2, unit_price=20),  # type: ignore # noqa
        ]
        purchase = Purchase(
            store=self.store,
            id=purchase_id,
            items=items,
            buyer_id=uuid4(),
            status=PurchaseStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = purchase

        # When
        await self.service.update_purchase_status(
            self.store.id, purchase_id, PurchaseStatus.IN_PROGRESS
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.store.id, purchase_id))
        purchase.status = PurchaseStatus.IN_PROGRESS
        purchase.payment_url = None  # type: ignore
        self.repository.save.assert_called_once_with(purchase)
        self.products_service.update_stock.assert_not_called()