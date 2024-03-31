from decimal import Decimal
import logging
from typing import Any, Literal, Sequence, TypedDict
from asyncio import gather

from fastapi import Depends, status
from fastapi.encoders import jsonable_encoder
from httpx import URL, AsyncClient, Timeout

from app.exceptions.products import ProductNotFound
from app.exceptions.purchases import (
    CantPurchaseFromOwnStore,
    OutsideDeliveryRange,
    PurchaseNotFound,
    StoreNotReady,
)
from app.exceptions.users import Forbidden
from app.models.purchases import Purchase, PurchaseItem, PurchaseStatus
from app.models.products import Product, ProductRead
from app.models.stores import Store
from app.models.util import Coordinates, Id, distance_squared
from app.repositories.purchases import PurchasesRepository
from app.services.products import ProductsService
from app.config import settings
from app.services.stores import StoresService
from app.services.users import UsersService

REQUEST_TIMEOUT = Timeout(5, read=45)


class PurchaseItemData(TypedDict):
    title: str
    currency_id: Literal["ARS"]
    picture_url: str | None
    description: str
    quantity: int
    unit_price: Decimal


class PurchasesService:
    def __init__(
        self,
        stores_service: StoresService = Depends(),
        products_service: ProductsService = Depends(),
        users_service: UsersService = Depends(),
        purchases_repo: PurchasesRepository = Depends(),
    ):
        self.stores_service = stores_service
        self.products_service = products_service
        self.users_service = users_service
        self.purchases_repo = purchases_repo

    # TODO:
    # - tests
    # - routes and exception handlers for routes
    # - update state from notification

    async def get_purchase(self, store_id: Id, purchase_id: Id, user_id: Id) -> Purchase:
        purchase = await self.purchases_repo.get_by_id((store_id, purchase_id))
        if purchase is None:
            raise PurchaseNotFound
        if user_id not in (purchase.buyer_id, purchase.store.owner_id):
            raise Forbidden
        return purchase

    async def get_store_purchases(
        self, store_id: Id, user_id: Id, limit: int, skip: int
    ) -> tuple[Sequence[Purchase], int]:
        store = await self.stores_service.get_store_by_id(store_id)
        if user_id != store.owner_id:
            raise Forbidden
        purchases = await self.purchases_repo.get_all(store_id=store_id, limit=limit, skip=skip)
        amount = await self.purchases_repo.count_all(store_id=store_id)
        return purchases, amount

    async def get_user_purchases(
        self, user_id: Id, limit: int, skip: int
    ) -> tuple[Sequence[Purchase], int]:
        purchases = await self.purchases_repo.get_all(buyer_id=user_id, limit=limit, skip=skip)
        amount = await self.purchases_repo.count_all(buyer_id=user_id)
        return purchases, amount

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
        if store.owner_id == user_id:
            raise CantPurchaseFromOwnStore

        purchase = Purchase(
            store=store,
            status=PurchaseStatus.CREATED,
            buyer_id=user_id,
            delivery_address_id=delivery_address_id,
        )

        _, (items, payload) = await gather(
            self.__check_purchase_conditions(store, user_id, delivery_address_id, token),
            self.__build_order(purchase.id, store.products, products_quantities),
        )
        purchase.items = items

        logging.debug(f"Creating preference for payment:\n{payload}")

        async with AsyncClient(
            headers={"Authorization": f"Bearer {token}"}, timeout=REQUEST_TIMEOUT
        ) as client:
            url = URL(
                settings.PAYMENTS_SERVICE_URL + "/payment",
                params={
                    "user_to_be_payed_id": str(store.owner_id),
                },
            )
            r = await client.post(url, json=payload)
            if r.status_code == status.HTTP_404_NOT_FOUND:
                raise StoreNotReady
            r.raise_for_status()
            purchase.payment_url = r.json()

        await self.purchases_repo.save(purchase)
        return purchase

    async def __check_purchase_conditions(
        self, store: Store, user_id: Id, delivery_address_id: Id, token: str
    ) -> None:
        if store.address is None:
            raise StoreNotReady

        user_coords = await self.users_service.get_user_address_coordinates(
            user_id, delivery_address_id, token
        )

        if (
            distance_squared(
                Coordinates(latitude=store.address.latitude, longitude=store.address.longitude),
                user_coords,
            )
            > store.delivery_range_km**2
        ):
            raise OutsideDeliveryRange

    async def __build_order(
        self, order_id: Id, products: Sequence[Product], products_quantities: dict[Id, int]
    ) -> tuple[Sequence[PurchaseItem], dict[str, Any]]:
        products_map = {p.id: p for p in products if p.id in products_quantities}
        if len(products_map) != len(products_quantities):
            raise ProductNotFound

        products_read = await self.products_service.get_products_read(products_map.values())
        store: Store = products[0].store

        total_cost = Decimal(0)
        x = await gather(
            *(
                self.__build_order_item(products_map[p.id], p, products_quantities[p.id])
                for p in products_read
            )
        )
        items: list[PurchaseItem]
        items_data: list[PurchaseItemData]
        items, items_data = map(list, zip(*x))
        total_cost = sum(
            (item["unit_price"] * item["quantity"] for item in items_data), start=Decimal(0)
        )

        return items, jsonable_encoder(
            {
                "payment_data": {
                    "external_reference": order_id,
                    "type": "P",
                    "items": items_data,
                    "marketplace_fee": total_cost * settings.FEE_PERCENTAGE / 100,
                    "shipments": {
                        "cost": store.shipping_cost,
                        "mode": "not_specified",
                    },
                },
            }
        )

    async def __build_order_item(
        self, product: Product, product_read: ProductRead, quantity: int
    ) -> tuple[PurchaseItem, PurchaseItemData]:
        await self.products_service.update_stock(product, -quantity)

        unit_price = product.price * (100 - product.percent_off) / 100
        purchase_item_data: PurchaseItemData = {
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
