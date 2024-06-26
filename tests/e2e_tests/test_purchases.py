from uuid import UUID, uuid4

from httpx import URL
from pytest_httpx import HTTPXMock
from app.config import settings

from app.models.stores import Store
from app.models.payments import PaymentStatus
from app.models.util import Id
from tests.factories.product_factories import ProductCreateFactory
from tests.factories.store_factories import StoreCreateFactory
from tests.tests_setup import BaseAPITestCase, GetUserCoordinatesMock


class TestPurchasesRoute(BaseAPITestCase):
    def setup_method(self) -> None:
        self.store_create_json_data = StoreCreateFactory.build().model_dump(mode="json")
        self.product_create_json_data = ProductCreateFactory.build(available=None).model_dump(
            mode="json"
        )

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

    async def test_purchase_store_has_not_linked_payment_account(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
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

        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 409

    async def test_purchase_one_item_invalid_address(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()

        await self.change_store_owner(store["id"])

        quantities = {product["id"]: 1}

        address_id = uuid4()
        mock_get_user_coordinates(address_id, True)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 404

    async def test_purchase_one_item(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()

        store_owner = await self.change_store_owner(store["id"])
        store["owner_id"] = str(store_owner)

        quantities = {product["id"]: 1}

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        preference_url = "http://payment.com"
        httpx_mock.add_response(url=url, json={"url": preference_url})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201
        data = r.json()

        assert data["payment_url"] == preference_url
        assert data["payment_status"] == "created"
        assert data["store"] == store
        assert data["buyer_id"] == str(self.user_id)
        assert data["delivery_address_id"] == str(address_id)
        assert len(data["items"]) == 1
        assert data["items"][0]["product"] == product

    async def test_purchase_one_item_and_get_my_purchases(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
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
        preference_url = "http://payment.com"
        httpx_mock.add_response(url=url, json={"url": preference_url})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201
        purchase_id = r.json()["id"]

        r_get = await self.client.get("/stores/purchases/me")
        assert r_get.status_code == 200
        data = r_get.json()
        assert len(data["purchases"]) == 1
        assert data["purchases"][0]["id"] == purchase_id

    async def test_purchase_one_item_reduces_stock(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        self.product_create_json_data["available"] = 5
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()

        store_owner = await self.change_store_owner(store["id"])

        quantities = {product["id"]: 2}

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})

        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201

        r_product_get = await self.client.get(f"/stores/{store['id']}/products/{product['id']}")
        assert r_product_get.status_code == 200
        assert (
            r_product_get.json()["available"]
            == self.product_create_json_data["available"] - quantities[product["id"]]
        )

    async def test_purchase_one_item_does_not_reduces_stock_if_fails(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        self.product_create_json_data["available"] = 5
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()

        store_owner = await self.change_store_owner(store["id"])

        quantities = {product["id"]: 2}

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, status_code=404)

        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 409

        r_product_get = await self.client.get(f"/stores/{store['id']}/products/{product['id']}")
        assert r_product_get.status_code == 200
        assert r_product_get.json()["available"]

    async def test_cant_update_purchase_without_api_key(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        self.product_create_json_data["available"] = 5
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()
        store_owner = await self.change_store_owner(store["id"])
        quantities = {product["id"]: 2}
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201
        purchase_id = r.json()["id"]

        r = await self.client.patch(
            f"/stores/{store['id']}/purchases/{purchase_id}",
            json={"status": PaymentStatus.IN_PROGRESS},
        )
        assert r.status_code == 401

    async def test_can_update_purchase_to_in_progress(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        self.product_create_json_data["available"] = 5
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()
        store_owner = await self.change_store_owner(store["id"])
        quantities = {product["id"]: 2}
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201
        p = r.json()
        assert p["payment_status"] == PaymentStatus.CREATED

        r_patch = await self.client.patch(
            f"/stores/{store['id']}/purchases/{p['id']}",
            headers={"api-key": settings.PAYMENTS_API_KEY},
            json={"status": PaymentStatus.IN_PROGRESS},
        )
        assert r_patch.status_code == 202

        r_get = await self.client.get(f"/stores/{store['id']}/purchases/{p['id']}")
        assert r_get.status_code == 200
        data = r_get.json()
        assert data["payment_status"] == PaymentStatus.IN_PROGRESS
        assert data.get("payment_url", None) is None

    async def test_can_update_purchase_to_completed(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        self.product_create_json_data["available"] = 5
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()
        store_owner = await self.change_store_owner(store["id"])
        quantities = {product["id"]: 2}
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201
        p = r.json()
        assert p["payment_status"] == PaymentStatus.CREATED

        httpx_mock.add_response(url=settings.USERS_SERVICE_URL + "/messages", status_code=204)
        httpx_mock.add_response(
            url=settings.USERS_SERVICE_URL + f"/users/{p["buyer_id"]}",
            json={"name": "John"}
        )

        r_patch = await self.client.patch(
            f"/stores/{store['id']}/purchases/{p['id']}",
            headers={"api-key": settings.PAYMENTS_API_KEY},
            json={"status": PaymentStatus.COMPLETED},
        )
        assert r_patch.status_code == 202

        r_get = await self.client.get(f"/stores/{store['id']}/purchases/{p['id']}")
        assert r_get.status_code == 200
        data = r_get.json()
        assert data["payment_status"] == PaymentStatus.COMPLETED
        assert data.get("payment_url", None) is None

    async def test_can_update_purchase_to_cancelled_and_restores_stock(
        self, httpx_mock: HTTPXMock, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store = r_store.json()
        self.product_create_json_data["available"] = 5
        r_product = await self.client.post(
            f"/stores/{store['id']}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        product = r_product.json()
        store_owner = await self.change_store_owner(store["id"])
        quantities = {product["id"]: 2}
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(store_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/stores/{store['id']}/purchases",
            json=quantities,
            params={"delivery_address_id": str(address_id)},
        )
        assert r.status_code == 201
        p = r.json()
        assert p["payment_status"] == PaymentStatus.CREATED

        r_patch = await self.client.patch(
            f"/stores/{store['id']}/purchases/{p['id']}",
            headers={"api-key": settings.PAYMENTS_API_KEY},
            json={"status": PaymentStatus.CANCELLED},
        )
        assert r_patch.status_code == 202

        r_get = await self.client.get(f"/stores/{store['id']}/purchases/{p['id']}")
        assert r_get.status_code == 200
        data = r_get.json()
        assert data["payment_status"] == PaymentStatus.CANCELLED
        assert data.get("payment_url", None) is None

        r_product_get = await self.client.get(f"/stores/{store['id']}/products/{product['id']}")
        assert r_product_get.status_code == 200
        assert r_product_get.json()["available"] == self.product_create_json_data["available"]
