import json
from tests.tests_setup import BaseAPITestCase

from app.models.stores import Store
from tests.fixtures.stores import valid_store, invalid_store


class TestStoresRoute(BaseAPITestCase):
    async def test_create_valid_store(self) -> None:
        response = await self.client.post("/stores", json=valid_store)

        assert response.status_code == 201

        response_text = json.loads(response.text)
        assert response_text["id"] is not None
        assert response_text["name"] == "test store"

        store_db: Store = await self.db.get(Store, response_text["id"])
        assert_store_db_equals_response(store_db, response_text)
        assert store_db.created_at is not None
        assert store_db.updated_at is not None

    async def test_create_invalid_store(self) -> None:
        response = await self.client.post("/stores", json=invalid_store)

        assert response.status_code == 400


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
