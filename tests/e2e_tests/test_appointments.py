from typing import Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from httpx import URL, Response
import pytest
from pytest_httpx import HTTPXMock

from app.config import settings
from app.models.services import Service, DayOfWeek, AppointmentSlotsBase
from app.models.payments import PaymentStatus
from app.models.util import Id
from tests.factories.service_factories import ServiceCreateFactory
from tests.tests_setup import BaseAPITestCase, GetUserCoordinatesMock
from tests.util import CustomMatcher


class TestAppointmentsRoute(BaseAPITestCase):
    def setup_method(self) -> None:
        self.service_create_json_data = ServiceCreateFactory.build(
            appointment_days_in_advance=3
        ).model_dump(mode="json")
        self.tz = ZoneInfo(self.service_create_json_data["timezone"])
        self.appointment_date = (datetime.now(self.tz) + timedelta(days=1)).date()
        appointment_day = DayOfWeek.from_weekday(self.appointment_date.weekday())
        self.service_create_json_data["appointment_slots"] = [
            {
                "start_day": appointment_day,
                "start_time": "08:00",
                "appointment_duration": "00:30",
                "appointment_price": 50,
                "end_day": appointment_day,
                "end_time": "09:00",
                "max_appointments_per_slot": 12,
            }
        ]
        self.first_appointment = {
            "start": datetime.combine(self.appointment_date, time(8, 0)).isoformat(),
            "animal_id": str(uuid4()),
        }

    async def change_service_owner(
        self, service_id: str | Id, new_owner: str | Id | None = None
    ) -> Id:
        service = await self.db.get(Service, service_id)
        assert service
        if new_owner is None:
            service.owner_id = uuid4()
        elif isinstance(new_owner, str):
            service.owner_id = UUID(new_owner)
        else:
            service.owner_id = new_owner
        self.db.add(service)
        await self.db.flush()
        return service.owner_id

    def mock_animal_validation_manual(self, httpx_mock: HTTPXMock, animal_id: Id | str) -> None:
        def callback(*args: Any, **kwargs: Any) -> Response:
            return Response(200, json={"owner": str(self.user_id)})

        httpx_mock.add_callback(
            callback,
            url=f"{settings.ANIMALS_SERVICE_URL}/animals/{animal_id}",
            method="GET",
        )

    @pytest.fixture
    def mock_animal_validation(self, httpx_mock: HTTPXMock) -> None:
        self.mock_animal_validation_manual(httpx_mock, self.first_appointment["animal_id"])

    async def test_get_available_appointments(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()
        r = await self.client.get(f"/services/{service['id']}/appointments/available")
        assert r.status_code == 200
        available = r.json()

        def check_slots_configuration(slots_configuration: dict[str, Any]) -> None:
            assert AppointmentSlotsBase.model_validate(
                slots_configuration
            ) == AppointmentSlotsBase.model_validate(
                self.service_create_json_data["appointment_slots"][0]
            )

        def check_available_appointments(available_appointments: list[dict[str, Any]]) -> None:
            assert [
                {
                    "start": datetime.fromisoformat(a["start"]),
                    "end": datetime.fromisoformat(a["end"]),
                    "amount": a["amount"],
                }
                for a in available_appointments
            ] == [
                {
                    "start": datetime.combine(self.appointment_date, time(8, 0), self.tz),
                    "end": datetime.combine(self.appointment_date, time(8, 30), self.tz),
                    "amount": 12,
                },
                {
                    "start": datetime.combine(self.appointment_date, time(8, 30), self.tz),
                    "end": datetime.combine(self.appointment_date, time(9, 0), self.tz),
                    "amount": 12,
                },
            ]

        assert available == [
            {
                "slots_configuration": CustomMatcher(check_slots_configuration),
                "available_appointments": CustomMatcher(check_available_appointments),
            }
        ]

    async def test_get_appointment_service_not_exists(self) -> None:
        r = await self.client.get(f"/services/{uuid4()}/appointments/{uuid4()}")
        assert r.status_code == 404

    async def test_get_appointment_not_exists(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = r_service.json()["id"]
        r = await self.client.get(f"/services/{service_id}/appointments/{uuid4()}")
        assert r.status_code == 404

    async def test_get_service_appointments_empty(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = r_service.json()["id"]
        r = await self.client.get(f"/services/{service_id}/appointments")
        assert r.status_code == 200
        assert r.json() == {"appointments": [], "amount": 0}

    async def test_get_service_appointments_not_service_owner(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = r_service.json()["id"]

        await self.change_service_owner(service_id)

        r = await self.client.get(f"/services/{service_id}/appointments")
        assert r.status_code == 403

    async def test_get_my_appointments_empty(self) -> None:
        r = await self.client.get("/services/appointments/me")
        assert r.status_code == 200
        assert r.json() == {"appointments": [], "amount": 0}

    async def test_appointment_service_not_exists(self) -> None:
        r = await self.client.post(
            f"/services/{uuid4()}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(uuid4())},
        )
        assert r.status_code == 404

    async def test_cant_create_appointment_from_self(self, mock_animal_validation: None) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = r_service.json()["id"]

        r = await self.client.post(
            f"/services/{service_id}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(uuid4())},
        )
        assert r.status_code == 403

    async def test_appointment_service_has_not_linked_payment_account(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        httpx_mock.add_response(url=url, status_code=404)

        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 409

    async def test_create_appointment_invalid_address(
        self, mock_get_user_coordinates: GetUserCoordinatesMock, mock_animal_validation: None
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        await self.change_service_owner(service["id"])

        address_id = uuid4()
        mock_get_user_coordinates(address_id, True)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 404

    async def test_create_appointment_animal_id_not_exists(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        service["owner_id"] = str(service_owner)

        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        httpx_mock.add_response(
            url=f"{settings.ANIMALS_SERVICE_URL}/animals/{self.first_appointment['animal_id']}",
            status_code=404,
        )

        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 400

    async def test_create_appointment_animal_id_different_owner(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        service["owner_id"] = str(service_owner)

        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        httpx_mock.add_response(
            url=f"{settings.ANIMALS_SERVICE_URL}/animals/{self.first_appointment['animal_id']}",
            json={"owner": str(uuid4())},
        )

        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 400

    async def test_create_appointment(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        service["owner_id"] = str(service_owner)

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        preference_url = "http://payment.com"
        httpx_mock.add_response(url=url, json={"url": preference_url})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        data = r.json()

        assert data["payment_url"] == preference_url
        assert data["payment_status"] == "created"
        assert data["service"] == service
        assert data["customer_id"] == str(self.user_id)
        assert data["customer_address_id"] == str(address_id)

    async def test_create_appointment_and_get_my_appointments(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        preference_url = "http://payment.com"
        httpx_mock.add_response(url=url, json={"url": preference_url})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        appointment_id = r.json()["id"]

        r_get = await self.client.get("/services/appointments/me")
        assert r_get.status_code == 200
        data = r_get.json()
        assert len(data["appointments"]) == 1
        assert data["appointments"][0]["id"] == appointment_id

    async def test_create_appointment_and_get_my_appointments_with_animal_filter(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        preference_url = "http://payment.com"
        httpx_mock.add_response(url=url, json={"url": preference_url})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        animal_id = self.first_appointment["animal_id"]
        self.mock_animal_validation_manual(httpx_mock, animal_id)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        appointment_id = r.json()["id"]

        r_2 = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r_2.status_code == 201
        appointment_id_2 = r_2.json()["id"]

        self.first_appointment["animal_id"] = str(uuid4())
        self.mock_animal_validation_manual(httpx_mock, self.first_appointment["animal_id"])
        r_3 = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r_3.status_code == 201

        r_get = await self.client.get("/services/appointments/me", params={"animal_id": animal_id})
        assert r_get.status_code == 200
        data = r_get.json()
        assert len(data["appointments"]) == 2
        assert set(a["id"] for a in data["appointments"]) == {appointment_id, appointment_id_2}

    async def test_create_appointment_and_get_my_appointments_with_category_filter(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        self.service_create_json_data["category"] = "walking"
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        self.service_create_json_data["category"] = "health"
        r_service_2 = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service_2.status_code == 201
        service_2 = r_service_2.json()

        service_owner = await self.change_service_owner(service["id"])
        await self.change_service_owner(service_2["id"], service_owner)

        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        preference_url = "http://payment.com"
        httpx_mock.add_response(url=url, json={"url": preference_url})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)

        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201

        r_2 = await self.client.post(
            f"/services/{service_2['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r_2.status_code == 201
        appointment_id_2 = r_2.json()["id"]

        r_get = await self.client.get(
            "/services/appointments/me", params={"service_category": "health"}
        )
        assert r_get.status_code == 200
        data = r_get.json()
        assert len(data["appointments"]) == 1
        assert data["appointments"][0]["id"] == appointment_id_2

    async def test_cant_update_appointment_without_api_key(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        appointment_id = r.json()["id"]

        r = await self.client.patch(
            f"/services/{service['id']}/appointments/{appointment_id}",
            json={"status": PaymentStatus.IN_PROGRESS},
        )
        assert r.status_code == 401

    async def test_can_update_appointment_to_in_progress(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        p = r.json()
        assert p["payment_status"] == PaymentStatus.CREATED

        r_patch = await self.client.patch(
            f"/services/{service['id']}/appointments/{p['id']}",
            headers={"api-key": settings.PAYMENTS_API_KEY},
            json={"status": PaymentStatus.IN_PROGRESS},
        )
        assert r_patch.status_code == 202

        r_get = await self.client.get(f"/services/{service['id']}/appointments/{p['id']}")
        assert r_get.status_code == 200
        data = r_get.json()
        assert data["payment_status"] == PaymentStatus.IN_PROGRESS
        assert data.get("payment_url", None) is None

    async def test_can_update_appointment_to_completed(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        p = r.json()
        assert p["payment_status"] == PaymentStatus.CREATED

        r_patch = await self.client.patch(
            f"/services/{service['id']}/appointments/{p['id']}",
            headers={"api-key": settings.PAYMENTS_API_KEY},
            json={"status": PaymentStatus.COMPLETED},
        )
        assert r_patch.status_code == 202

        r_get = await self.client.get(f"/services/{service['id']}/appointments/{p['id']}")
        assert r_get.status_code == 200
        data = r_get.json()
        assert data["payment_status"] == PaymentStatus.COMPLETED
        assert data.get("payment_url", None) is None

    async def test_can_update_appointment_to_cancelled(
        self,
        httpx_mock: HTTPXMock,
        mock_get_user_coordinates: GetUserCoordinatesMock,
        mock_animal_validation: None,
    ) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service = r_service.json()

        service_owner = await self.change_service_owner(service["id"])
        url = URL(
            settings.PAYMENTS_SERVICE_URL + "/payment",
            params={
                "user_to_be_payed_id": str(service_owner),
            },
        )
        httpx_mock.add_response(url=url, json={"url": "http://payment.com"})
        address_id = uuid4()
        mock_get_user_coordinates(address_id)
        r = await self.client.post(
            f"/services/{service['id']}/appointments",
            json=self.first_appointment,
            params={"user_address_id": str(address_id)},
        )
        assert r.status_code == 201
        p = r.json()
        assert p["payment_status"] == PaymentStatus.CREATED

        r_patch = await self.client.patch(
            f"/services/{service['id']}/appointments/{p['id']}",
            headers={"api-key": settings.PAYMENTS_API_KEY},
            json={"status": PaymentStatus.CANCELLED},
        )
        assert r_patch.status_code == 202

        r_get = await self.client.get(f"/services/{service['id']}/appointments/{p['id']}")
        assert r_get.status_code == 200
        data = r_get.json()
        assert data["payment_status"] == PaymentStatus.CANCELLED
        assert data.get("payment_url", None) is None
