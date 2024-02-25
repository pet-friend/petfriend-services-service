from typing import Sequence, Any
import json
from uuid import uuid4
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

    async def test_create_address_with_all_fields(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 201
        response_text: dict[str, Any] = json.loads(r_address.text)
        address: Address | None = await self.db.get(Address, response_text["service_id"])
        response_text.pop("latitude")
        response_text.pop("longitude")

        assert address is not None
        assert address.created_at is not None
        assert address.updated_at is not None
        assert response_text.pop("service_id") == service_id
        assert response_text == self.address_create_json_data

    async def test_create_address_with_required_fields(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.HOUSE

        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 201
        response_text: dict[str, Any] = json.loads(r_address.text)
        address: Address | None = await self.db.get(Address, response_text["service_id"])
        response_text.pop("latitude")
        response_text.pop("longitude")

        assert address is not None
        assert address.created_at is not None
        assert address.updated_at is not None
        assert response_text.pop("service_id") == service_id
        assert response_text == self.address_create_json_data

    async def test_create_address_without_some_required_fields(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        del self.address_create_json_data["country_code"]

        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 400
        response_text: dict[str, Any] = json.loads(r_address.text)

        assert response_text == {"detail": {"country_code": ["Field required"]}}

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()
        assert len(addresses_db) == 0

    async def test_create_address_with_invalid_country_code_should_return_400(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["country_code"] = "xx"
        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )

        assert r_address.status_code == 400

        response_text: dict[str, Any] = json.loads(r_address.text)
        assert "Invalid country alpha2 code" in response_text["detail"]["country_code"][0]

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()
        assert len(addresses_db) == 0

    async def test_cant_create_multiple_addresses(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        address_create_json_data_2 = AddressCreateFactory.build(
            country_code="AR", type="other"
        ).model_dump(mode="json")

        r_address_1 = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address_1.status_code == 201

        r_address_2 = await self.client.post(
            f"/addresses/{service_id}", json=address_create_json_data_2
        )
        assert r_address_2.status_code == 409

    async def test_create_and_get(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        r_post = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_post.status_code == 201
        r_get = await self.client.get(f"/addresses/{service_id}")
        assert r_get.status_code == 200
        response_text: dict[str, Any] = json.loads(r_get.text)
        response_text.pop("latitude")
        response_text.pop("longitude")

        assert response_text.pop("service_id") == service_id
        assert response_text.items() == self.address_create_json_data.items()

    async def test_can_create_with_put(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        r_address = await self.client.put(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 200
        response_text: dict[str, Any] = json.loads(r_address.text)
        address: Address | None = await self.db.get(Address, response_text["service_id"])
        response_text.pop("latitude")
        response_text.pop("longitude")

        assert address is not None
        assert address.created_at is not None
        assert address.updated_at is not None
        assert response_text.pop("service_id") == service_id
        assert response_text == self.address_create_json_data

    async def test_create_and_modify_address(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 201
        response_text: dict[str, Any] = json.loads(r_address.text)

        response_text["apartment"] = "2B"
        r_address_2 = await self.client.put(f"/addresses/{service_id}", json=response_text)
        assert r_address_2.status_code == 200
        response_text_2: dict[str, Any] = json.loads(r_address_2.text)
        assert response_text_2 == response_text

    async def test_create_delete_get_address_returns_404(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        r_post = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_post.status_code == 201

        r_delete = await self.client.delete(f"/addresses/{service_id}")
        assert r_delete.status_code == 204

        r_get = await self.client.get(f"/addresses/{service_id}")
        assert r_get.status_code == 404

    async def test_delete_address_not_exists_returns_404(self) -> None:
        service_id = str(uuid4())

        r_delete = await self.client.delete(f"/addresses/{service_id}")
        assert r_delete.status_code == 404

    @pytest.mark.invalidaddress
    async def test_create_non_existent_address(self) -> None:
        response = await self.client.post("/stores", json=valid_store)
        assert response.status_code == 201
        service_id = response.json()["id"]

        self.address_create_json_data["type"] = AddressType.APARTMENT
        self.address_create_json_data["apartment"] = "1A"

        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 422

    async def test_create_address_no_service(self) -> None:
        service_id = uuid4()

        r_address = await self.client.post(
            f"/addresses/{service_id}", json=self.address_create_json_data
        )
        assert r_address.status_code == 404

        addresses_db: Sequence[Address] = (await self.db.exec(select(Address))).all()
        assert len(addresses_db) == 0
