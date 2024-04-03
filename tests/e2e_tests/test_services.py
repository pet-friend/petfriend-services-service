import json
from typing import Any
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.services import Service
from tests.tests_setup import BaseAPITestCase
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
