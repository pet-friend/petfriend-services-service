from uuid import uuid4

import pytest
from app.config import settings

from app.models.stores import Store
from app.models.util import Id
from tests.factories.address_factories import AddressCreateFactory
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from tests.tests_setup import BaseAPITestCase


@pytest.mark.usefixtures("mock_google_maps")
class TestStoresProductsRoute(BaseAPITestCase):
    def setup_method(self) -> None:
        self.store_create_json_data = StoreCreateFactory.build(address=None).model_dump(mode="json")
        self.store_create_json_data["address"] = AddressCreateFactory.build(
            country_code="AR", type="other"
        ).model_dump(mode="json")
        self.product_create_json_data = ProductCreateFactory.build().model_dump(mode="json")

    async def change_store_owner(self, store_id: Id, new_owner: Id | None = None) -> Id:
        store = await self.db.get(Store, store_id)
        assert store
        store.owner_id = new_owner or uuid4()
        self.db.add(store)
        await self.db.flush()
        return store.owner_id

    async def test_get_fee(self) -> None:
        r = await self.client.get("/fee")
        assert r.status_code == 200
        assert r.json() == str(settings.FEE_PERCENTAGE)

    async def test_get_purchase_store_not_exists(self) -> None:
        r = await self.client.get(f"/stores/{uuid4()}/purchases/{uuid4()}")
        assert r.status_code == 404

    async def test_get_purchase_not_exists(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        r = await self.client.get(f"/stores/{store_id}/purchases/{uuid4()}")
        assert r.status_code == 404

    async def test_get_store_purchases_empty(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        r = await self.client.get(f"/stores/{store_id}/purchases")
        assert r.status_code == 200
        assert r.json() == {"purchases": [], "amount": 0}

    async def test_get_store_purchases_not_store_owner(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]

        await self.change_store_owner(store_id)

        r = await self.client.get(f"/stores/{store_id}/purchases")
        assert r.status_code == 403

    async def test_get_my_purchases_empty(self) -> None:
        r = await self.client.get("/stores/purchases/me")
        assert r.status_code == 200
        assert r.json() == {"purchases": [], "amount": 0}

    # async def test_purchase_one_product(self) -> None:
    #     r_store = await self.client.post("/stores", json=self.store_create_json_data)
    #     assert r_store.status_code == 201
    #     store_id = r_store.json()["id"]
    #     r_product = await self.client.post(
    #         f"/stores/{store_id}/products", json=self.product_create_json_data
    #     )
    #     assert r_product.status_code == 201

    async def test_purchase_store_not_exists(self) -> None:
        r = await self.client.post(
            f"/stores/{uuid4()}/purchases",
            json={str(uuid4()): 1},
            params={"ship_to_address_id": str(uuid4())},
        )
        assert r.status_code == 404

    async def test_cant_purchase_from_self(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product_id = r_product.json()["id"]

        r = await self.client.post(
            f"/stores/{store_id}/purchases",
            json={product_id: 1},
            params={"ship_to_address_id": str(uuid4())},
        )
        assert r.status_code == 403

    async def test_purchase_product_not_exists(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201

        await self.change_store_owner(store_id)

        r = await self.client.post(
            f"/stores/{store_id}/purchases",
            json={str(uuid4()): 1},
            params={"ship_to_address_id": str(uuid4())},
        )
        assert r.status_code == 404
