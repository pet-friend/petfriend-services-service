from typing import Sequence, Any
import json
from unittest.mock import patch
from uuid import uuid4

from sqlmodel import select

from app.models.stores import Store
from app.models.addresses import Address, AddressType
from app.models.util import Coordinates
from tests.factories.address_factories import AddressCreateFactory
from tests.fixtures.stores import valid_store
from tests.tests_setup import BaseAPITestCase


class TestAddresses(BaseAPITestCase):
    def setup_method(self) -> None:
        self.address_create_json_data = AddressCreateFactory.build(
            country_code="AR", type="other"
        ).model_dump(mode="json")

    async def test_post_address_with_all_fields(self, mock_google_maps: None) -> None:
        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.post("/stores", json=data)
        assert response.status_code == 201

        response_text: dict[str, Any] = json.loads(response.text)
        address_response = response_text["address"]

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()

        assert len(addresses_db) == 1
        address_db = addresses_db[0]
        assert address_db.created_at is not None
        assert address_db.updated_at is not None
        assert address_response.items() < address_db.model_dump(mode="json").items()

    async def test_post_address_with_required_fields(self, mock_google_maps: None) -> None:
        self.address_create_json_data["type"] = AddressType.HOUSE
        self.address_create_json_data.pop("apartment", None)

        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.post("/stores", json=data)
        assert response.status_code == 201

        response_text: dict[str, Any] = json.loads(response.text)
        address_response = response_text["address"]

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()

        assert len(addresses_db) == 1
        address_db = addresses_db[0]
        assert address_db.created_at is not None
        assert address_db.updated_at is not None
        assert address_response.items() < address_db.model_dump(mode="json").items()

    async def test_post_address_without_some_required_fields(self) -> None:
        self.address_create_json_data.pop("country_code", None)

        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.post("/stores", json=data)
        assert response.status_code == 400

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()

        assert len(addresses_db) == 0

    async def test_create_and_get(self, mock_google_maps: None) -> None:
        self.address_create_json_data["type"] = AddressType.HOUSE
        self.address_create_json_data["apartment"] = None

        data = {**valid_store, "address": self.address_create_json_data}

        r_post = await self.client.post("/stores", json=data)
        assert r_post.status_code == 201

        store_id = r_post.json()["id"]

        r_get = await self.client.get(f"/stores/{store_id}")
        assert r_get.status_code == 200

        response_text: dict[str, Any] = json.loads(r_get.text)["address"]
        response_text.pop("latitude")
        response_text.pop("longitude")

        assert response_text.items() == self.address_create_json_data.items()

    async def test_put_address_with_all_fields(self, mock_google_maps: None) -> None:
        r_0 = await self.client.post("/stores", json=valid_store)
        assert r_0.status_code == 201
        store_id = r_0.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.put(f"/stores/{store_id}", json=data)
        assert response.status_code == 200

        response_text: dict[str, Any] = json.loads(response.text)
        address_response = response_text["address"]

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()

        assert len(addresses_db) == 1
        address_db = addresses_db[0]
        assert address_db.created_at is not None
        assert address_db.updated_at is not None
        assert address_response.items() < address_db.model_dump(mode="json").items()

    async def test_create_non_existent_address(self, mock_google_maps_error: None) -> None:
        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.post("/stores", json=data)
        assert response.status_code == 422

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()

        assert len(addresses_db) == 0

    async def test_post_delete_address_should_remove_from_db(self, mock_google_maps: None) -> None:
        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.post("/stores", json=data)
        assert response.status_code == 201
        store_id = response.json()["id"]
        addresses_db_1: Sequence[Address] = (await self.db.exec(select(Address))).all()
        assert len(addresses_db_1) == 1

        response = await self.client.delete(f"/stores/{store_id}")
        assert response.status_code == 204
        addresses_db_2: Sequence[Address] = (await self.db.exec(select(Address))).all()
        assert len(addresses_db_2) == 0

    async def test_get_nearby(self) -> None:
        store_base: dict[str, Any] = {"owner_id": uuid4(), "shipping_cost": 0, "description": ":D"}
        addr_base = self.address_create_json_data

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

        with patch("app.services.users.UsersService.get_user_address_coordinates") as mock:
            coords_obelisco = Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145)
            mock.return_value = coords_obelisco
            response = await self.client.get(
                "/stores/nearby", params={"user_address_id": str(uuid4())}
            )
            assert response.status_code == 200
            stores = response.json()["stores"]

        assert {s["name"] for s in stores} == {store_1.name, store_3.name}
