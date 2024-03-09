from typing import Sequence, Any
import json
import pytest

from sqlmodel import select

from app.models.addresses import Address, AddressType
from tests.factories.address_factories import AddressCreateFactory
from tests.fixtures.stores import valid_store
from tests.tests_setup import BaseAPITestCase


class TestAddressesRoute(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.address_create_json_data = AddressCreateFactory.build(
            country_code="AR", type="other"
        ).model_dump(mode="json")

    async def test_post_address_with_all_fields(self) -> None:
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

    async def test_post_address_with_required_fields(self) -> None:
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

    async def test_create_and_get(self) -> None:
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

    async def test_put_address_with_all_fields(self) -> None:
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

    @pytest.mark.invalidaddress
    async def test_create_non_existent_address(self) -> None:
        data = {**valid_store, "address": self.address_create_json_data}

        response = await self.client.post("/stores", json=data)
        assert response.status_code == 422

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()

        assert len(addresses_db) == 0

    async def test_post_delete_address_should_remove_from_db(self) -> None:
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
