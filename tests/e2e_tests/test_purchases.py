from unittest.mock import patch
from uuid import UUID, uuid4

from httpx import URL
import pytest
from pytest_httpx import HTTPXMock
from app.config import settings

from app.models.stores import Store
from app.models.util import Coordinates, Id
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

    async def change_store_owner(self, store_id: str | Id, new_owner: str | Id | None = None) -> Id:
        store = await self.db.get(Store, store_id)
        assert store
        if new_owner is None:
            store.owner_id = uuid4()
        elif isinstance(new_owner, str):
            store.owner_id = UUID(new_owner)
        else:
            store.owner_id = new_owner
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

    async def test_purchase_store_not_exists(self) -> None:
        r = await self.client.post(
            f"/stores/{uuid4()}/purchases",
            json={str(uuid4()): 1},
            params={"delivery_address_id": str(uuid4())},
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
            params={"delivery_address_id": str(uuid4())},
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
            params={"delivery_address_id": str(uuid4())},
        )
        assert r.status_code == 404

    async def test_purchase_store_has_no_address(self, httpx_mock: HTTPXMock) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()

        store_owner = await self.change_store_owner(store["id"])

        quantities = {product["id"]: 1}

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, status_code=404)

        with patch("app.services.users.UsersService.get_user_address_coordinates") as mock:
            mock.return_value = Coordinates(latitude=0, longitude=0)
            r = await self.client.post(
                f"/stores/{store['id']}/purchases",
                json=quantities,
                params={"delivery_address_id": str(uuid4())},
            )
        assert r.status_code == 409

    async def test_purchase_one_item(self, httpx_mock: HTTPXMock) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()

        store_owner = await self.change_store_owner(store["id"])

        quantities = {product["id"]: 1}

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        payment_url = "http://payment.com"
        httpx_mock.add_response(url=url, json=payment_url)
        address_id = str(uuid4())

        with patch("app.services.users.UsersService.get_user_address_coordinates") as mock:
            mock.return_value = Coordinates(latitude=0, longitude=0)
            r = await self.client.post(
                f"/stores/{store['id']}/purchases",
                json=quantities,
                params={"delivery_address_id": address_id},
            )
        assert r.status_code == 200
        data = r.json()

        assert data["payment_url"] == payment_url
        assert data["status"] == "created"
        assert data["store_id"] == store["id"]
        assert data["buyer_id"] == str(self.user_id)
        assert data["delivery_address_id"] == address_id
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == product["id"]
