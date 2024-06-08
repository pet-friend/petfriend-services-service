import json
from typing import Any
from uuid import uuid4

from app.models.addresses import Address
from app.models.stores import Store
from app.models.util import Coordinates
from tests.tests_setup import BaseAPITestCase, GetUserCoordinatesMock
from tests.fixtures.stores import valid_store, valid_store2, invalid_store


class TestStoresRoute(BaseAPITestCase):
    async def test_create_valid_store(self) -> None:
        response = await self.client.post("/stores", json=valid_store)

        assert response.status_code == 201

        response_text = json.loads(response.text)
        assert response_text["id"] is not None
        assert response_text["name"] == "test store"

        store_db: Store | None = await self.db.get(Store, response_text["id"])
        assert store_db
        assert_store_db_equals_response(store_db, response_text)
        assert store_db.owner_id == self.user_id
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

    async def test_get_stores_name_filter(self) -> None:
        create_1 = valid_store.copy()
        create_1["name"] = "happy store"
        response = await self.client.post("/stores", json=create_1)
        assert response.status_code == 201
        expected_id = response.json()["id"]

        create_2 = valid_store.copy()
        create_2["name"] = "sad store"
        response_2 = await self.client.post("/stores", json=create_2)
        assert response_2.status_code == 201

        response_get = await self.client.get("/stores", params={"name": "happy"})
        assert response_get.status_code == 200

        data = response_get.json()
        assert len(data["stores"]) == 1
        assert data["stores"][0]["id"] == expected_id

    async def test_get_my_stores_name_filter(self) -> None:
        create_1 = valid_store.copy()
        create_1["name"] = "happy store"
        response = await self.client.post("/stores", json=create_1)
        assert response.status_code == 201
        expected_id = response.json()["id"]

        create_2 = valid_store.copy()
        create_2["name"] = "sad store"
        response_2 = await self.client.post("/stores", json=create_2)
        assert response_2.status_code == 201

        response_get = await self.client.get("/stores/me", params={"name": "happy"})
        assert response_get.status_code == 200

        data = response_get.json()
        assert len(data["stores"]) == 1
        assert data["stores"][0]["id"] == expected_id

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

    async def test_get_store_filtering_by_owner(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201

        # get existing store
        response2 = await self.client.get(f"/stores?owner_id={self.user_id}")
        assert response2.status_code == 200

        # get non existing store
        response3 = await self.client.get(f"/stores?owner_id={uuid4()}")
        assert response3.status_code == 200

        # check that the store is in the first response
        response_text = json.loads(response2.text)
        assert len(response_text["stores"]) == 1

        # check that the store is not in the second response
        response_text2 = json.loads(response3.text)
        assert len(response_text2["stores"]) == 0

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

    async def test_delete_store_not_owner_is_forbidden(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        store_id = response.json()["id"]

        # Change store owner
        store = await self.db.get(Store, store_id)
        assert store
        store.owner_id = uuid4()
        self.db.add(store)
        await self.db.flush()

        response2 = await self.client.delete(f"/stores/{store_id}")
        assert response2.status_code == 403

    async def test_get_nearby_stores(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        store_base: dict[str, Any] = {"owner_id": uuid4(), "shipping_cost": 0, "description": ":D"}
        addr_base: Any = valid_store["address"]

        # Tienda 1: a menos de 500m del obelisco, radio de 1km -> debería aparecer
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        store_1 = Store(**store_base, address=address_1, name="Tienda 1", delivery_range_km=1)

        # Tienda 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        store_2 = Store(**store_base, address=address_2, name="Tienda 2", delivery_range_km=3)

        # Tienda 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        store_3 = Store(**store_base, address=address_3, name="Tienda 3", delivery_range_km=4)

        self.db.add(store_1)
        self.db.add(store_2)
        self.db.add(store_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/stores/nearby", params={"user_address_id": str(address_id)}
        )
        assert response.status_code == 200
        stores = response.json()["stores"]
        assert {s["name"] for s in stores} == {store_1.name, store_3.name}

    async def test_get_nearby_stores_name_filter(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        store_base: dict[str, Any] = {"owner_id": uuid4(), "shipping_cost": 0, "description": ":D"}
        addr_base: Any = valid_store["address"]

        # Tienda 1: a menos de 500m del obelisco, radio de 1km -> filtrada por nombre
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        store_1 = Store(**store_base, address=address_1, name="Tienda AAA", delivery_range_km=1)

        # Tienda 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        store_2 = Store(**store_base, address=address_2, name="Tienda BBB", delivery_range_km=3)

        # Tienda 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        store_3 = Store(**store_base, address=address_3, name="Tienda BBB 2", delivery_range_km=4)

        self.db.add(store_1)
        self.db.add(store_2)
        self.db.add(store_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/stores/nearby", params={"user_address_id": str(address_id), "name": "BBB"}
        )
        assert response.status_code == 200
        stores = response.json()["stores"]
        assert {s["name"] for s in stores} == {store_3.name}

    async def test_get_nearby_stores_owner_filter(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        store_base: dict[str, Any] = {"shipping_cost": 0, "description": ":D"}
        addr_base: Any = valid_store["address"]
        owner_id1 = uuid4()
        owner_id2 = uuid4()
        owner_id3 = uuid4()

        # Tienda 1: a menos de 500m del obelisco, radio de 1km -> debería aparecer
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        store_1 = Store(
            **store_base,
            address=address_1,
            name="Tienda 1",
            delivery_range_km=1,
            owner_id=owner_id1,
        )

        # Tienda 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        store_2 = Store(
            **store_base,
            address=address_2,
            name="Tienda 2",
            delivery_range_km=3,
            owner_id=owner_id2,
        )

        # Tienda 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        store_3 = Store(
            **store_base,
            address=address_3,
            name="Tienda 3",
            delivery_range_km=4,
            owner_id=owner_id3,
        )

        self.db.add(store_1)
        self.db.add(store_2)
        self.db.add(store_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/stores/nearby",
            params={"user_address_id": str(address_id), "owner_id": str(owner_id1)},
        )
        assert response.status_code == 200
        stores = response.json()["stores"]
        assert {s["owner_id"] for s in stores} == {str(owner_id1)}


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
