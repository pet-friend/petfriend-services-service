from decimal import Decimal
import logging
from typing import Any, Sequence
from asyncio import gather

from fastapi import Depends
from httpx import Timeout

from app.exceptions.products import ProductNotFound
from app.exceptions.purchases import PurchaseNotFound
from app.exceptions.users import Forbidden
from app.models.preferences import StorePurchasePaymentData, PreferenceItem, PaymentType
from app.models.stores import (
    Store,
    Product,
    ProductRead,
    Purchase,
    PurchaseRead,
    PurchaseItem,
    PurchaseItemRead,
)
from app.models.payments import PaymentStatus, PaymentStatusUpdate
from app.models.util import Id
from app.repositories.stores import PurchasesRepository
from app.config import settings
from ..users import Notification, UsersService
from ..payments import PaymentsService
from .stores import StoresService
from .products import ProductsService

REQUEST_TIMEOUT = Timeout(5, read=45)
FORBIDDEN_STATUS_CHANGES = [PaymentStatus.COMPLETED, PaymentStatus.CANCELLED]


class PurchasesService:
    def __init__(
        self,
        stores_service: StoresService = Depends(),
        products_service: ProductsService = Depends(),
        users_service: UsersService = Depends(),
        payments_service: PaymentsService = Depends(),
        purchases_repo: PurchasesRepository = Depends(),
    ):
        self.stores_service = stores_service
        self.products_service = products_service
        self.users_service = users_service
        self.payments_service = payments_service
        self.purchases_repo = purchases_repo

    async def get_purchase(self, store_id: Id, purchase_id: Id, user_id: Id) -> Purchase:
        purchase = await self.purchases_repo.get_by_id((store_id, purchase_id))
        if purchase is None:
            raise PurchaseNotFound
        if user_id not in (purchase.buyer_id, purchase.store.owner_id):
            raise Forbidden
        return purchase

    async def get_purchases_read(self, *purchases: Purchase) -> list[PurchaseRead]:
        return await gather(*(self.__readable(p) for p in purchases))

    async def get_store_purchases(
        self, store_id: Id, user_id: Id, limit: int, skip: int
    ) -> tuple[Sequence[Purchase], int]:
        store = await self.stores_service.get_store_by_id(store_id)
        if user_id != store.owner_id:
            raise Forbidden
        purchases = await self.get_purchases(limit, skip, store_id=store_id)
        amount = await self.purchases_repo.count_all(store_id=store_id)
        return purchases, amount

    async def get_user_purchases(
        self, user_id: Id, limit: int | None, skip: int, **filters: Any
    ) -> tuple[Sequence[Purchase], int]:
        purchases = await self.get_purchases(limit, skip, buyer_id=user_id, **filters)
        amount = await self.purchases_repo.count_all(buyer_id=user_id, **filters)
        return purchases, amount

    async def get_purchases(
        self, limit: int | None = None, skip: int = 0, **filters: Any
    ) -> Sequence[Purchase]:
        return await self.purchases_repo.get_all(limit=limit, skip=skip, **filters)

    async def purchase(
        self,
        store_id: Id,
        products_quantities: dict[Id, int],
        user_id: Id,
        delivery_address_id: Id,
        token: str,
    ) -> Purchase:
        """
        Returns a payment URL for the user to complete the purchase.
        """
        if len(products_quantities) == 0:
            raise ProductNotFound
        store = await self.stores_service.get_store_by_id(store_id)

        purchase = Purchase(
            store=store,
            payment_status=PaymentStatus.CREATED,
            buyer_id=user_id,
            delivery_address_id=delivery_address_id,
        )

        _, (items, payload) = await gather(
            # check_payment_conditions does not use SQLAlchemy's
            # AsyncSession so it's safe to run it concurrently
            self.payments_service.check_payment_conditions(
                store, user_id, delivery_address_id, token
            ),
            self.__build_order(purchase.id, store.products, products_quantities),
        )
        purchase.items = items

        logging.debug(f"Creating preference for payment:\n{payload}")

        purchase.payment_url = await self.payments_service.create_preference(
            payload, store.owner_id, token
        )
        await self.purchases_repo.save(purchase)
        await self.__send_order_notification(purchase)
        return purchase

    async def update_purchase_status(
        self, store_id: Id, purchase_id: Id, new_status: PaymentStatusUpdate
    ) -> None:
        purchase = await self.purchases_repo.get_by_id((store_id, purchase_id))
        if purchase is None:
            raise PurchaseNotFound

        if not await self.payments_service.update_payment_status(purchase, new_status):
            return

        if new_status == PaymentStatus.CANCELLED:
            # Restore stock
            for item in purchase.items:
                await self.products_service.update_stock(item.product, item.quantity)

        await self.purchases_repo.save(purchase)
        await self.__send_order_notification(purchase)
        await self.__send_event_message(purchase)

    async def __send_order_notification(self, purchase: Purchase) -> None:
        text = await self.__get_notification_text(purchase)
        if text is None:
            return
        store_read = (await self.stores_service.get_stores_read(purchase.store))[0]
        await self.users_service.send_notification(
            purchase.store.owner_id,
            Notification(
                source="purchase",
                title=text[0],
                message=text[1],
                image=store_read.image_url,
                payload={
                    "purchase_id": str(purchase.id),
                    "store_id": str(purchase.store.id),
                    "type": "purchase",
                    "payment_status": purchase.payment_status,
                },
            ),
        )

    async def __get_notification_text(self, purchase: Purchase) -> tuple[str, str] | None:
        total_cost = sum((i.unit_price * i.quantity for i in purchase.items), start=Decimal(0))
        if purchase.payment_status == PaymentStatus.CREATED:
            return (
                f"[{purchase.store.name}] Tenés una nueva compra",
                f"Pago pendiente por ${total_cost}",
            )
        if purchase.payment_status == PaymentStatus.COMPLETED:
            return (
                f"[{purchase.store.name}] Se completó el pago de una compra",
                f"Pago confirmado por ${total_cost}. Coordiná la entrega con el comprador.",
            )
        if purchase.payment_status == PaymentStatus.CANCELLED:
            return (
                f"[{purchase.store.name}] Se canceló una compra",
                f"El pago por ${total_cost} fue cancelado. Se restauró el stock de tus productos.",
            )
        return None

    async def __send_event_message(self, purchase: Purchase) -> None:
        text = await self.__get_event_message_text(purchase)
        if text is None:
            return
        await self.users_service.send_event_message(purchase.buyer_id, text)

    async def __get_event_message_text(self, purchase: Purchase) -> str | None:
        if purchase.payment_status == PaymentStatus.COMPLETED:
            buyer = await self.users_service.get_by_id(purchase.buyer_id)
            return (
                f"{buyer["name"]} realizó una compra en {purchase.store.name}"
            )
        return None

    async def __build_order(
        self, order_id: Id, products: Sequence[Product], products_quantities: dict[Id, int]
    ) -> tuple[list[PurchaseItem], StorePurchasePaymentData]:
        products_map = {p.id: p for p in products if p.id in products_quantities}
        if len(products_map) != len(products_quantities):
            raise ProductNotFound

        products_read = await self.products_service.get_products_read(*products_map.values())
        store: Store = products[0].store

        total_cost = Decimal(0)
        items: list[PurchaseItem] = []
        items_data: list[PreferenceItem] = []
        for p in products_read:
            # Note: don't run this concurrently since we can't use the
            # AsyncSession to modify the stock in different tasks
            item, item_data = await self.__build_order_item(
                products_map[p.id], p, products_quantities[p.id]
            )
            items.append(item)
            items_data.append(item_data)
            total_cost += item_data["unit_price"] * item_data["quantity"]

        return items, {
            "service_reference": order_id,
            "type": PaymentType.STORE_PURCHASE,
            "preference_data": {
                "items": items_data,
                "marketplace_fee": total_cost * settings.FEE_PERCENTAGE / 100,
                "shipments": {
                    "cost": store.shipping_cost,
                    "mode": "not_specified",
                },
                "metadata": {
                    "store_id": store.id,
                    "purchase_id": order_id,
                    "type": PaymentType.STORE_PURCHASE,
                },
            },
        }

    async def __build_order_item(
        self, product: Product, product_read: ProductRead, quantity: int
    ) -> tuple[PurchaseItem, PreferenceItem]:
        await self.products_service.update_stock(product, -quantity)

        unit_price = product.price * (100 - product.percent_off) / 100
        purchase_item_data: PreferenceItem = {
            "title": product_read.name,
            "currency_id": "ARS",
            "picture_url": product_read.image_url,
            "description": product_read.description,
            "quantity": quantity,
            "unit_price": unit_price,
        }
        purchase_item = PurchaseItem(
            store_id=product.store_id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
        )  # type: ignore
        return purchase_item, purchase_item_data

    async def __readable(self, purchase: Purchase) -> PurchaseRead:
        store_promise = self.stores_service.get_stores_read(purchase.store)
        products_promise = self.products_service.get_products_read(
            *(i.product for i in purchase.items)
        )
        stores, products = await gather(store_promise, products_promise)
        return PurchaseRead(
            **purchase.model_dump(),
            store=stores[0],
            items=[
                PurchaseItemRead(**item.model_dump(), product=products[i])
                for i, item in enumerate(purchase.items)
            ],
        )
