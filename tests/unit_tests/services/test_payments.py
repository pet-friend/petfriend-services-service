from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock
from datetime import datetime, timezone, time

from httpx import URL
import pytest
from pytest_httpx import HTTPXMock

from app.config import settings
from app.exceptions.users import Forbidden
from app.exceptions.payments import CollectorNotReady, OutsideBusinessRange, CantBuyFromOwnBusiness
from app.models.addresses import Address
from app.models.preferences import PaymentData, PaymentType
from app.models.services import Service, AppointmentSlots, Appointment
from app.models.stores import Store, Product, Purchase, PurchaseItem
from app.models.payments import PaymentStatus
from app.models.util import Coordinates
from app.services.payments import PaymentsService
from app.services.users import UsersService

from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from tests.factories.service_factories import ServiceCreateFactory


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
            store_id=self.store.id,
            store=self.store,
            **ProductCreateFactory.build().model_dump(),
        )
        self.store.products = [self.product]

        service_create = ServiceCreateFactory.build()
        self.service_model = Service(
            owner_id=self.owner_id,
            appointment_slots=[
                AppointmentSlots(**slot_create.model_dump())
                for slot_create in service_create.appointment_slots
            ],
            address=Address(latitude=0, longitude=0, **service_create.address.model_dump()),
            **service_create.model_dump(exclude={"address", "appointment_slots"}),
        )

        self.users_service = AsyncMock(spec=UsersService)
        self.service = PaymentsService(self.users_service)

    async def test_update_cancelled_purchase_should_raise(self) -> None:
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
            status=PaymentStatus.CANCELLED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        prev = purchase.model_dump(mode="json")

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(purchase, PaymentStatus.IN_PROGRESS)
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(purchase, PaymentStatus.COMPLETED)

        assert prev == purchase.model_dump(mode="json")

    async def test_update_cancelled_appointment_should_raise(self) -> None:
        # Given
        now = datetime.now(timezone.utc)
        appointment = Appointment(
            start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
            end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
            status=PaymentStatus.CANCELLED,
            customer_id=uuid4(),
        )
        prev = appointment.model_dump(mode="json")

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(appointment, PaymentStatus.IN_PROGRESS)
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(appointment, PaymentStatus.COMPLETED)

        assert prev == appointment.model_dump(mode="json")

    async def test_update_completed_purchase_should_raise(self) -> None:
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
            status=PaymentStatus.COMPLETED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        prev = purchase.model_dump(mode="json")

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(purchase, PaymentStatus.IN_PROGRESS)
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(purchase, PaymentStatus.CANCELLED)

        assert prev == purchase.model_dump(mode="json")

    async def test_update_completed_appointment_should_raise(self) -> None:
        # Given
        now = datetime.now(timezone.utc)
        appointment = Appointment(
            start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
            end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
            status=PaymentStatus.COMPLETED,
            customer_id=uuid4(),
        )
        prev = appointment.model_dump(mode="json")

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(appointment, PaymentStatus.IN_PROGRESS)
        with pytest.raises(Forbidden):
            await self.service.update_payment_status(appointment, PaymentStatus.CANCELLED)

        assert prev == appointment.model_dump(mode="json")

    async def test_update_payment_status_to_completed_should_update(self) -> None:
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
            status=PaymentStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )

        # When, Then
        assert await self.service.update_payment_status(purchase, PaymentStatus.IN_PROGRESS)
        assert purchase.status == PaymentStatus.IN_PROGRESS
        assert purchase.payment_url is None

        assert await self.service.update_payment_status(purchase, PaymentStatus.COMPLETED)
        assert purchase.status == PaymentStatus.COMPLETED

    async def test_update_payment_status_to_cancelled_should_update(self) -> None:
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
            status=PaymentStatus.CREATED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )

        # When, Then
        assert await self.service.update_payment_status(purchase, PaymentStatus.IN_PROGRESS)
        assert purchase.status == PaymentStatus.IN_PROGRESS
        assert purchase.payment_url is None
        assert await self.service.update_payment_status(purchase, PaymentStatus.CANCELLED)
        assert purchase.status == PaymentStatus.CANCELLED

    async def test_update_payment_status_same_status_should_not_update(self) -> None:
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
            status=PaymentStatus.COMPLETED,
            payment_url="http://payment.url",
            delivery_address_id=uuid4(),
        )
        prev = purchase.model_dump(mode="json")

        # When, Then
        assert not await self.service.update_payment_status(purchase, PaymentStatus.COMPLETED)

        assert prev == purchase.model_dump(mode="json")

    async def test_make_payment_from_self_should_raise(self) -> None:
        # Given
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=0, longitude=0
        )

        with pytest.raises(CantBuyFromOwnBusiness):
            await self.service.check_payment_conditions(self.store, self.owner_id, uuid4(), "token")

    async def test_make_payment_too_far_should_raise(self) -> None:
        # Given
        user_id = uuid4()
        address_id = uuid4()
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=50, longitude=50
        )

        # When, Then
        with pytest.raises(OutsideBusinessRange):
            await self.service.check_payment_conditions(self.store, user_id, address_id, "token")

        self.users_service.get_user_address_coordinates.assert_called_once_with(
            user_id, address_id, "token"
        )

    async def test_make_payment_ok_should_succeed(self) -> None:
        # Given
        user_id = uuid4()
        address_id = uuid4()
        self.users_service.get_user_address_coordinates.return_value = Coordinates(
            latitude=0, longitude=0
        )

        # When
        await self.service.check_payment_conditions(self.store, user_id, address_id, "token")

        # Then
        self.users_service.get_user_address_coordinates.assert_called_once_with(
            user_id, address_id, "token"
        )

    async def test_create_preference_payment_not_linked_should_raise(
        self, httpx_mock: HTTPXMock
    ) -> None:
        # Given
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

        data: PaymentData = {
            "type": PaymentType.STORE_PURCHASE,
            "service_reference": uuid4(),
            "preference_data": {
                "items": [
                    {
                        "title": "Product",
                        "quantity": 1,
                        "unit_price": Decimal(10),
                        "currency_id": "ARS",
                    }
                ],
                "metadata": {
                    "purchase_id": uuid4(),
                    "store_id": uuid4(),
                    "type": PaymentType.STORE_PURCHASE,
                },
            },
        }

        # When, Then
        with pytest.raises(CollectorNotReady):
            await self.service.create_preference(data, self.store.owner_id, token)

    async def test_create_preference_payment_returns_preference_url(
        self, httpx_mock: HTTPXMock
    ) -> None:
        # Given
        token = "token"
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(self.store.owner_id),
            },
        )
        payment_url = "http://url"
        httpx_mock.add_response(
            url=url, headers={"Authorization": f"Bearer {token}"}, status_code=200, json=payment_url
        )

        data: PaymentData = {
            "type": PaymentType.STORE_PURCHASE,
            "service_reference": uuid4(),
            "preference_data": {
                "items": [
                    {
                        "title": "Product",
                        "quantity": 1,
                        "unit_price": Decimal(10),
                        "currency_id": "ARS",
                    }
                ],
                "metadata": {
                    "purchase_id": uuid4(),
                    "store_id": uuid4(),
                    "type": PaymentType.STORE_PURCHASE,
                },
            },
        }

        # When, Then
        assert payment_url == await self.service.create_preference(data, self.store.owner_id, token)
