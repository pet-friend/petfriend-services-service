from typing import Any, Sequence
from uuid import uuid4

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from httpx import URL, AsyncClient, Timeout

from app.exceptions.products import ProductNotFound
from app.models.products import ProductRead
from app.models.util import Id
from app.services.products import ProductsService
from app.config import settings

REQUEST_TIMEOUT = Timeout(5, read=45)


class PurchasesService:
    def __init__(
        self,
        products_service: ProductsService = Depends(ProductsService),
    ):
        self.products_service = products_service

    async def purchase(self, store_id: Id, products_quantities: dict[Id, int], token: str) -> str:
        if len(products_quantities) == 0:
            raise ProductNotFound
        products = await self.products_service.get_store_products(store_id)
        store = products[0].store
        products_read = await self.products_service.get_products_read(
            p for p in products if p.id in products_quantities
        )

        if len(products_read) != len(products_quantities):
            raise ProductNotFound
        async with AsyncClient(
            headers={"Authorization": f"Bearer {token}"}, timeout=REQUEST_TIMEOUT
        ) as client:
            url = URL(
                settings.PAYMENTS_SERVICE_URL + "/payment",
                params={
                    "user_to_be_payed_id": str(store.owner_id),
                },
            )
            r = await client.post(url, json=self.build_payload(products_read, products_quantities))
            r.raise_for_status()
            return r.json()

    def build_payload(
        self, products: Sequence[ProductRead], products_quantities: dict[Id, int]
    ) -> dict[str, Any]:
        items = [
            {
                "title": p.name,
                "currency_id": "ARS",
                "picture_url": p.image_url,
                "description": p.description,
                "quantity": products_quantities[p.id],
                "unit_price": p.price * (1 - p.percent_off / 100),
            }
            for p in products
        ]
        total_cost = sum(i["unit_price"] * i["quantity"] for i in items)  # type: ignore
        return jsonable_encoder(
            {
                "payment_data": {
                    "external_reference": uuid4(),
                    "type": "P",
                    "items": items,
                    "marketplace_fee": total_cost * settings.FEE_PERCENTAGE / 100,
                }
            }
        )
