import json
from typing import Any
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.addresses import Address
from app.models.services import Service
from app.models.util import Coordinates
from tests.tests_setup import BaseAPITestCase, GetUserCoordinatesMock
from tests.factories.service_factories import ServiceCreateFactory


class TestServicesRoute(BaseAPITestCase):
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service_create = ServiceCreateFactory().build().model_dump(mode="json")

    async def test_create_valid_service(self) -> None:
        response = await self.client.post("/services", json=self.service_create)

        assert response.status_code == 201

        response_text = json.loads(response.text)
        assert response_text["id"] is not None
        assert response_text["name"] == self.service_create["name"]

        service_db: Service | None = await self.db.get(Service, response_text["id"])
        assert service_db
        assert_service_db_equals_response(service_db, response_text)
        assert service_db.owner_id == self.user_id
        assert service_db.created_at is not None
        assert service_db.updated_at is not None

    async def test_create_invalid_service(self) -> None:
        invalid_service = self.service_create
        invalid_service["name"] = None
        response = await self.client.post("/services", json=invalid_service)

        assert response.status_code == 400

    async def test_get_services(self) -> None:
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201
        response2 = await self.client.get("/services")
        assert response2.status_code == 200

        response_text = json.loads(response2.text)
        await _verify_paginated_response(self.db, response_text, 1, 1)

    async def test_get_services_filters(self) -> None:
        self.service_create["name"] = "happy service"
        self.service_create["category"] = "grooming"
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201
        expected_id = response.json()["id"]

        self.service_create["name"] = "sad service"
        self.service_create["category"] = "grooming"
        response_2 = await self.client.post("/services", json=self.service_create)
        assert response_2.status_code == 201

        self.service_create["name"] = "happy service 2"
        self.service_create["category"] = "other"
        response_2 = await self.client.post("/services", json=self.service_create)
        assert response_2.status_code == 201

        response_get = await self.client.get(
            "/services", params={"name": "happy", "category": "grooming"}
        )
        assert response_get.status_code == 200

        data = response_get.json()
        assert len(data["services"]) == 1
        assert data["services"][0]["id"] == expected_id

    async def test_get_my_services_filters(self) -> None:
        self.service_create["name"] = "happy service"
        self.service_create["category"] = "grooming"
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201
        expected_id = response.json()["id"]

        self.service_create["name"] = "sad service"
        self.service_create["category"] = "grooming"
        response_2 = await self.client.post("/services", json=self.service_create)
        assert response_2.status_code == 201

        self.service_create["name"] = "happy service 2"
        self.service_create["category"] = "other"
        response_2 = await self.client.post("/services", json=self.service_create)
        assert response_2.status_code == 201

        response_get = await self.client.get(
            "/services/me", params={"name": "happy", "category": "grooming"}
        )
        assert response_get.status_code == 200

        data = response_get.json()
        assert len(data["services"]) == 1
        assert data["services"][0]["id"] == expected_id

    async def test_get_services_with_pagination(self) -> None:
        valid_service = self.service_create
        response = await self.client.post("/services", json=valid_service)
        assert response.status_code == 201
        response2 = await self.client.post("/services", json=valid_service)
        assert response2.status_code == 201
        response3 = await self.client.get("/services?limit=1&offset=1")
        assert response3.status_code == 200

        response_text = json.loads(response3.text)
        await _verify_paginated_response(self.db, response_text, 1, 2)

    async def test_get_service_by_id(self) -> None:
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201

        response_text = json.loads(response.text)
        response2 = await self.client.get(f"/services/{response_text['id']}")
        assert response2.status_code == 200

        response_text2 = json.loads(response2.text)
        assert_service_db_equals_response(
            await self.db.get(Service, response_text["id"]), response_text2
        )

    async def test_get_service_by_id_not_found(self) -> None:
        response = await self.client.get(f"/services/{uuid4()}")
        assert response.status_code == 404

    async def test_get_service_filtering_by_owner(self) -> None:
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201

        # get existing service
        response2 = await self.client.get(f"/services?owner_id={self.user_id}")
        assert response2.status_code == 200

        # get non existing service
        response3 = await self.client.get(f"/services?owner_id={uuid4()}")
        assert response3.status_code == 200

        # check that the service is in the first response
        response_text = json.loads(response2.text)
        assert len(response_text["services"]) == 1

        # check that the service is not in the second response
        response_text2 = json.loads(response3.text)
        assert len(response_text2["services"]) == 0

    async def test_update_service(self) -> None:
        valid_service = self.service_create
        response = await self.client.post("/services", json=valid_service)
        assert response.status_code == 201

        valid_service["name"] = "new name"
        response_text = json.loads(response.text)
        response2 = await self.client.put(f"/services/{response_text['id']}", json=valid_service)
        assert response2.status_code == 200

        response_text2 = json.loads(response2.text)
        assert_service_db_equals_response(
            await self.db.get(Service, response_text["id"]), response_text2
        )

    async def test_update_service_not_found(self) -> None:
        response = await self.client.put(f"/services/{uuid4()}", json=self.service_create)
        assert response.status_code == 404

    async def test_delete_service(self) -> None:
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201

        response_text = json.loads(response.text)
        response2 = await self.client.delete(f"/services/{response_text['id']}")
        assert response2.status_code == 204

        assert await self.db.get(Service, response_text["id"]) is None

    async def test_delete_service_not_found(self) -> None:
        response = await self.client.delete(f"/services/{uuid4()}")
        assert response.status_code == 404

    async def test_delete_service_not_owner_is_forbidden(self) -> None:
        response = await self.client.post("/services", json=self.service_create)
        assert response.status_code == 201
        service_id = response.json()["id"]

        # Change service owner
        service = await self.db.get(Service, service_id)
        assert service
        service.owner_id = uuid4()
        self.db.add(service)
        await self.db.flush()

        response2 = await self.client.delete(f"/services/{service_id}")
        assert response2.status_code == 403

    async def test_get_nearby_services(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        service_base = {
            k: v
            for k, v in self.service_create.items()
            if k not in ("name", "address", "customer_range_km")
        }
        service_base["owner_id"] = self.user_id
        service_base["appointment_slots"] = []
        addr_base = self.service_create["address"]

        # Serv 1: a menos de 500m del obelisco, radio de 1km -> debería aparecer
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        service_1 = Service(**service_base, address=address_1, name="Serv 1", customer_range_km=1)

        # Serv 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        service_2 = Service(**service_base, address=address_2, name="Serv 2", customer_range_km=3)

        # Serv 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        service_3 = Service(**service_base, address=address_3, name="Serv 3", customer_range_km=4)

        self.db.add(service_1)
        self.db.add(service_2)
        self.db.add(service_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/services/nearby", params={"user_address_id": str(address_id)}
        )
        assert response.status_code == 200
        services = response.json()["services"]
        assert {s["name"] for s in services} == {service_1.name, service_3.name}

    async def test_get_nearby_services_name_filter(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        service_base = {
            k: v
            for k, v in self.service_create.items()
            if k not in ("name", "address", "customer_range_km")
        }
        service_base["owner_id"] = self.user_id
        service_base["appointment_slots"] = []
        addr_base = self.service_create["address"]

        # Serv 1: a menos de 500m del obelisco, radio de 1km -> filtrada por nombre
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        service_1 = Service(**service_base, address=address_1, name="Serv AAA", customer_range_km=1)

        # Serv 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        service_2 = Service(**service_base, address=address_2, name="Serv BBB", customer_range_km=3)

        # Serv 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        service_3 = Service(**service_base, address=address_3, name="Serv BBB", customer_range_km=4)

        self.db.add(service_1)
        self.db.add(service_2)
        self.db.add(service_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/services/nearby", params={"user_address_id": str(address_id), "name": "BBB"}
        )
        assert response.status_code == 200
        services = response.json()["services"]
        assert {s["name"] for s in services} == {service_3.name}

    async def test_get_nearby_services_owner_filter(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        service_base = {
            k: v
            for k, v in self.service_create.items()
            if k not in ("name", "address", "customer_range_km")
        }
        service_base["appointment_slots"] = []
        addr_base = self.service_create["address"]
        owner_id1 = uuid4()
        owner_id2 = uuid4()
        owner_id3 = uuid4()

        # Serv 1: a menos de 500m del obelisco, radio de 1km -> debería aparecer
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        service_1 = Service(
            **service_base,
            address=address_1,
            name="Serv 1",
            customer_range_km=1,
            owner_id=owner_id1,
        )

        # Serv 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        service_2 = Service(
            **service_base,
            address=address_2,
            name="Serv 2",
            customer_range_km=3,
            owner_id=owner_id2,
        )

        # Serv 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        service_3 = Service(
            **service_base,
            address=address_3,
            name="Serv 3",
            customer_range_km=4,
            owner_id=owner_id3,
        )

        self.db.add(service_1)
        self.db.add(service_2)
        self.db.add(service_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/services/nearby",
            params={"user_address_id": str(address_id), "owner_id": str(owner_id1)},
        )
        assert response.status_code == 200
        services = response.json()["services"]
        assert {s["owner_id"] for s in services} == {str(owner_id1)}


# Aux
async def _verify_paginated_response(
    db: AsyncSession, response_text: dict[str, Any], services_in_page: int, amount: int
) -> None:
    assert len(response_text["services"]) == services_in_page
    assert response_text["amount"] == amount

    for service in response_text["services"]:
        service_db: Service | None = await db.get(Service, service["id"])
        assert_service_db_equals_response(service_db, service)


def assert_service_db_equals_response(service_db: Service | None, response: dict[str, Any]) -> None:
    assert service_db
    assert str(service_db.id) == response["id"]
    assert service_db.name == response.get("name", None)
    assert service_db.description == response.get("description", None)
    assert str(service_db.owner_id) == response.get("owner_id", None)
