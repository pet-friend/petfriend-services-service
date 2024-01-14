import json
from uuid import uuid4
from tests.tests_setup import BaseAPITestCase

from app.models.stores import Store
from tests.fixtures.stores import valid_store, valid_store2, invalid_store


class TestStoresRoute(BaseAPITestCase):
    async def test_create_valid_store(self) -> None:
        response = await self.client.post("/stores", json=valid_store)

        assert response.status_code == 201

        response_text = json.loads(response.text)
        assert response_text["id"] is not None
        assert response_text["name"] == "test store"

        store_db: Store = await self.db.get(Store, response_text["id"])  # type: ignore
        assert_store_db_equals_response(store_db, response_text)
        assert store_db.created_at is not None
        assert store_db.updated_at is not None

    async def test_create_invalid_store(self) -> None:
        response = await self.client.post("/stores", json=invalid_store)

        assert response.status_code == 400

    async def test_create_store_with_existing_name(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        response2 = await self.client.post("/stores", json=valid_store)
        assert response2.status_code == 409

    async def test_get_stores(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        response2 = await self.client.get("/stores")
        assert response2.status_code == 200

        response_text = json.loads(response2.text)
        await _verify_paginated_response(self.db, response_text, 1, 1)

    async def test_get_stores_with_pagination(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        response2 = await self.client.post("/stores", json=valid_store2)
        assert response2.status_code == 201
        response3 = await self.client.get("/stores?limit=1&offset=1")
        assert response3.status_code == 200

        response_text = json.loads(response3.text)
        await _verify_paginated_response(self.db, response_text, 1, 2)

    async def test_get_store_by_id(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201

        response_text = json.loads(response.text)
        response2 = await self.client.get(f"/stores/{response_text['id']}")
        assert response2.status_code == 200

        response_text2 = json.loads(response2.text)
        assert_store_db_equals_response(
            await self.db.get(Store, response_text["id"]), response_text2
        )

    async def test_get_store_by_id_not_found(self) -> None:
        response = await self.client.get(f"/stores/{uuid4()}")
        assert response.status_code == 404

    async def test_update_store(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201

        response_text = json.loads(response.text)
        response2 = await self.client.put(f"/stores/{response_text['id']}", json=valid_store2)
        assert response2.status_code == 200

        response_text2 = json.loads(response2.text)
        assert_store_db_equals_response(
            await self.db.get(Store, response_text["id"]), response_text2
        )

    async def test_update_store_not_found(self) -> None:
        response = await self.client.put(f"/stores/{uuid4()}", json=valid_store)
        assert response.status_code == 404

    async def test_delete_store(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201

        response_text = json.loads(response.text)
        response2 = await self.client.delete(f"/stores/{response_text['id']}")
        assert response2.status_code == 204

        assert await self.db.get(Store, response_text["id"]) is None

    async def test_delete_store_not_found(self) -> None:
        response = await self.client.delete(f"/stores/{uuid4()}")
        assert response.status_code == 404


# Aux
async def _verify_paginated_response(db, response_text, stores_in_page, amount):  # type: ignore
    assert len(response_text["stores"]) == stores_in_page
    assert response_text["amount"] == amount

    for store in response_text["stores"]:
        store_db: Store = await db.get(Store, store["id"])
        assert_store_db_equals_response(store_db, store)


def assert_store_db_equals_response(store_db, response):  # type: ignore
    assert str(store_db.id) == response["id"]
    assert store_db.name == response.get("name", None)
    assert store_db.description == response.get("description", None)
    assert store_db.delivery_range_km == response.get("delivery_range_km", None)
