from decimal import Decimal
import logging
from typing import Any, Sequence
from asyncio import gather

from fastapi import Depends, status
from fastapi.encoders import jsonable_encoder
from httpx import URL, AsyncClient, Timeout

from app.exceptions.products import ProductNotFound
from app.exceptions.purchases import OutsideDeliveryRange, StoreNotReady
from app.models.purchases import Purchase, PurchaseItem, PurchaseStatus
from app.models.products import Product
from app.models.stores import Store
from app.models.util import Coordinates, Id, distance_squared
from app.repositories.purchases import PurchasesRepository
from app.services.products import ProductsService
from app.config import settings
from app.services.users import UsersService

REQUEST_TIMEOUT = Timeout(5, read=45)


class PurchasesService:
    def __init__(
        self,
        products_service: ProductsService = Depends(),
        users_service: UsersService = Depends(),
        purchases_repo: PurchasesRepository = Depends(),
    ):
        self.products_service = products_service
        self.users_service = users_service
        self.purchases_repo = purchases_repo

    # TODO:
    # - tests
    # - check that user can't buy from his own store?
    # - routes and exception handlers for routes
    # - update state from notification

    async def purchase(
        self,
        store_id: Id,
        products_quantities: dict[Id, int],
        user_id: Id,
        ship_to_address_id: Id,
        token: str,
    ) -> str:
        """
        Returns a payment URL for the user to complete the purchase.
        """
        if len(products_quantities) == 0:
            raise ProductNotFound
        products = await self.products_service.get_store_products(store_id)
        store: Store = products[0].store

        purchase = Purchase(store=store, state=PurchaseStatus.IN_PROGRESS)

        _, (items, payload) = await gather(
            self.check_purchase_conditions(store, user_id, ship_to_address_id, token),
            self.build_order(purchase.id, products, products_quantities),
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
            payment_url = r.json()

        await self.purchases_repo.save(purchase)
        return payment_url

    async def check_purchase_conditions(
        self, store: Store, user_id: Id, ship_to_address_id: Id, token: str
    ) -> None:
        if store.address is None:
            raise StoreNotReady

        user_coords = await self.users_service.get_user_address_coordinates(
            user_id, ship_to_address_id, token
        )

        if (
            distance_squared(
                Coordinates(latitude=store.address.latitude, longitude=store.address.longitude),
                user_coords,
            )
            > store.delivery_range_km**2
        ):
            raise OutsideDeliveryRange

    async def build_order(
        self, order_id: Id, products: Sequence[Product], products_quantities: dict[Id, int]
    ) -> tuple[list[PurchaseItem], dict[str, Any]]:
        products_read = await self.products_service.get_products_read(
            p for p in products if p.id in products_quantities
        )
        if len(products_read) != len(products_quantities):
            raise ProductNotFound

        store: Store = products[0].store

        total_cost = Decimal(0)
        json_items = []
        items = []
        for p in products_read:
            unit_price = p.price * (1 - p.percent_off / 100)
            total_cost += unit_price * products_quantities[p.id]
            json_items.append(
                {
                    "title": p.name,
                    "currency_id": "ARS",
                    "picture_url": p.image_url,
                    "description": p.description,
                    "quantity": products_quantities[p.id],
                    "unit_price": unit_price,
                }
            )
            items.append(
                PurchaseItem(
                    product_id=p.id, quantity=products_quantities[p.id], unit_price=unit_price
                )  # type: ignore
            )

        return items, jsonable_encoder(
            {
                "payment_data": {
                    "external_reference": order_id,
                    "type": "P",
                    "items": json_items,
                    "marketplace_fee": total_cost * settings.FEE_PERCENTAGE / 100,
                    "shipments": {
                        "cost": store.shipping_cost,
                        "mode": "not_specified",
                    },
                },
            }
        )
