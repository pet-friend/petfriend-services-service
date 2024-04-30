from decimal import Decimal
import json
import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.models.payments import PaymentStatus
from app.models.services import Service, Appointment
from app.models.services.services import ServiceReview
from app.models.util import Id

from tests.tests_setup import BaseAPITestCase
from tests.factories.service_factories import ServiceCreateFactory
from tests.factories.review_factories import ReviewCreateFactory


class TestServicesRoute(BaseAPITestCase):
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service_create = ServiceCreateFactory().build().model_dump(mode="json")
        self.review_create = ReviewCreateFactory().build().model_dump(mode="json")

        now = datetime.now(timezone.utc)
        self.appointment = Appointment(
            animal_id=uuid4(),
            service_id=uuid4(),
            customer_id=self.user_id,
            payment_status=PaymentStatus.COMPLETED,
            start=now - timedelta(hours=24),
            end=now - timedelta(hours=20),
            customer_address_id=uuid4(),
            price=Decimal(100),
        )

    async def test_create_valid_review(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        await self.change_service_owner(service_id)
        self.appointment.service_id = service_id
        self.db.add(self.appointment)
        await self.db.flush()
        await self.db.commit()

        r_post = await self.client.post(f"/services/{service_id}/reviews", json=self.review_create)
        assert r_post.status_code == 201
        review = r_post.json()

        assert review["service_id"] == service_id
        assert review["reviewer_id"] == str(self.user_id)
        assert review["comment"] == self.review_create["comment"]
        assert review["rating"] == self.review_create["rating"]

    async def test_cant_create_two_reviews(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        await self.change_service_owner(service_id)
        self.appointment.service_id = service_id
        self.db.add(self.appointment)
        await self.db.flush()
        await self.db.commit()

        r_post = await self.client.post(f"/services/{service_id}/reviews", json=self.review_create)
        assert r_post.status_code == 201

        r_post_2 = await self.client.post(
            f"/services/{service_id}/reviews", json=self.review_create
        )
        assert r_post_2.status_code == 409

    async def test_create_and_get_valid_review(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        await self.change_service_owner(service_id)
        self.appointment.service_id = service_id
        self.db.add(self.appointment)
        await self.db.flush()
        await self.db.commit()

        r_post = await self.client.post(f"/services/{service_id}/reviews", json=self.review_create)
        assert r_post.status_code == 201

        r_get = await self.client.get(f"/services/{service_id}/reviews/me")
        assert r_get.status_code == 200
        review = r_get.json()

        assert review["service_id"] == service_id
        assert review["reviewer_id"] == str(self.user_id)
        assert review["comment"] == self.review_create["comment"]
        assert review["rating"] == self.review_create["rating"]

    async def test_create_review_without_requirements(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        await self.change_service_owner(service_id)

        # no appointments
        r_post = await self.client.post(f"/services/{service_id}/reviews", json=self.review_create)
        assert r_post.status_code == 403

    async def test_get_multiple_reviews(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        data = json.loads(r_service.text)
        assert data.get("reviews_average_rating", None) is None
        service_id = data["id"]

        for i in range(1, 6):
            user_id = uuid4()
            review = ServiceReview(service_id=service_id, reviewer_id=user_id, rating=i, comment="")
            self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(f"/services/{service_id}/reviews", params={"limit": 3})
        assert r_get.status_code == 200

        result = r_get.json()
        assert result["amount"] == 5
        assert len(result["reviews"]) == 3
        assert result["average_rating"] == 3

        r_get_service = await self.client.get(f"/services/{service_id}")
        assert r_get_service.status_code == 200

        assert r_get_service.json()["reviews_average_rating"] == 3

    async def test_get_multiple_reviews_sort_rating_asc(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        for i in (3, 1, 5, 2, 4):
            user_id = uuid4()
            review = ServiceReview(
                service_id=service_id, reviewer_id=user_id, rating=i, comment=str(i)
            )
            self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(
            f"/services/{service_id}/reviews",
            params={"limit": 3, "sort_by": "rating", "sort_order": "asc", "offset": 1},
        )
        assert r_get.status_code == 200

        result = r_get.json()
        assert result["amount"] == 5
        assert result["average_rating"] == 3
        assert [r["rating"] for r in result["reviews"]] == [2, 3, 4]

    async def test_get_multiple_reviews_sort_rating_desc(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        for i in (3, 1, 5, 2, 4):
            user_id = uuid4()
            review = ServiceReview(
                service_id=service_id, reviewer_id=user_id, rating=i, comment=str(i)
            )
            self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(
            f"/services/{service_id}/reviews",
            params={"limit": 3, "sort_by": "rating", "sort_order": "desc"},
        )
        assert r_get.status_code == 200

        result = r_get.json()
        assert result["amount"] == 5
        assert result["average_rating"] == 3
        assert [r["rating"] for r in result["reviews"]] == [5, 4, 3]

    async def test_get_multiple_reviews_sort_created_at_desc(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        ratings = (3, 1, 5, 2, 4)
        for i in ratings:
            user_id = uuid4()
            review = ServiceReview(
                service_id=service_id, reviewer_id=user_id, rating=i, comment=str(i)
            )
            self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(
            f"/services/{service_id}/reviews",
            params={"limit": 3, "sort_by": "created_at", "sort_order": "desc"},  # newest first
        )
        assert r_get.status_code == 200

        result = r_get.json()
        assert result["amount"] == 5
        assert result["average_rating"] == 3
        assert tuple(r["rating"] for r in result["reviews"]) == ratings[::-1][:3]

    async def test_get_multiple_reviews_sort_created_at_asc(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        ratings = (3, 1, 5, 2, 4)
        for i in ratings:
            user_id = uuid4()
            review = ServiceReview(
                service_id=service_id, reviewer_id=user_id, rating=i, comment=str(i)
            )
            self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(
            f"/services/{service_id}/reviews",
            params={"limit": 3, "sort_by": "created_at", "sort_order": "asc"},  # oldest first
        )
        assert r_get.status_code == 200

        result = r_get.json()
        assert result["amount"] == 5
        assert result["average_rating"] == 3
        assert tuple(r["rating"] for r in result["reviews"]) == ratings[:3]

    async def test_other_user_review(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        user_id = uuid4()
        review = ServiceReview(service_id=service_id, reviewer_id=user_id, rating=5, comment=":D")
        self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(f"/services/{service_id}/reviews/{user_id}")
        assert r_get.status_code == 200

        result = r_get.json()
        assert result["service_id"] == service_id
        assert result["reviewer_id"] == str(user_id)
        assert result["rating"] == 5
        assert result["comment"] == ":D"

    async def test_other_user_review_not_exists_not_found(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        user_id = uuid4()

        r_get = await self.client.get(f"/services/{service_id}/reviews/{user_id}")
        assert r_get.status_code == 404

    async def test_other_user_review_service_not_exists_not_found(self) -> None:
        service_id = uuid4()
        user_id = uuid4()

        r_get = await self.client.get(f"/services/{service_id}/reviews/{user_id}")
        assert r_get.status_code == 404

    async def test_update_review(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        await self.change_service_owner(service_id)
        self.appointment.service_id = service_id
        self.db.add(self.appointment)
        await self.db.flush()
        await self.db.commit()

        r_post = await self.client.post(f"/services/{service_id}/reviews", json=self.review_create)
        assert r_post.status_code == 201

        self.review_create["comment"] = "Updated comment"
        self.review_create["rating"] = (self.review_create["rating"] + 3) % 5 + 1

        r_put = await self.client.put(f"/services/{service_id}/reviews/me", json=self.review_create)
        assert r_put.status_code == 200
        updated_review = r_put.json()

        assert updated_review["service_id"] == service_id
        assert updated_review["reviewer_id"] == str(self.user_id)
        assert updated_review["comment"] == self.review_create["comment"]
        assert updated_review["rating"] == self.review_create["rating"]

    async def test_update_review_not_found(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        response = await self.client.put(
            f"/services/{service_id}/reviews/me", json=self.review_create
        )
        assert response.status_code == 404

    async def test_update_review_service_not_found(self) -> None:
        service_id = uuid4()
        response = await self.client.put(
            f"/services/{service_id}/reviews/me", json=self.review_create
        )
        assert response.status_code == 404

    async def test_delete_review(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        await self.change_service_owner(service_id)
        self.appointment.service_id = service_id
        self.db.add(self.appointment)
        await self.db.flush()
        await self.db.commit()

        r_post = await self.client.post(f"/services/{service_id}/reviews", json=self.review_create)
        assert r_post.status_code == 201

        r_delete = await self.client.delete(f"/services/{service_id}/reviews/me")
        assert r_delete.status_code == 204

        assert await self.db.get(ServiceReview, (service_id, self.user_id)) is None

    async def test_delete_review_not_found(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        response = await self.client.delete(f"/services/{service_id}/reviews/me")
        assert response.status_code == 404

    async def test_delete_review_service_not_found(self) -> None:
        service_id = uuid4()
        response = await self.client.delete(f"/services/{service_id}/reviews/me")
        assert response.status_code == 404

    async def test_delete_service_deletes_reviews(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        user_id = uuid4()
        review = ServiceReview(service_id=service_id, reviewer_id=user_id, rating=5, comment=":D")
        self.db.add(review)
        await self.db.flush()
        await self.db.commit()

        r_get = await self.client.get(f"/services/{service_id}/reviews/{user_id}")
        assert r_get.status_code == 200

        r_delete = await self.client.delete(f"/services/{service_id}")
        assert r_delete.status_code == 204

        r_get_2 = await self.client.get(f"/services/{service_id}/reviews/{user_id}")
        assert r_get_2.status_code == 404

        assert await self.db.get(ServiceReview, (service_id, user_id)) is None

    async def change_service_owner(self, service_id: Id, new_owner: Id | None = None) -> Id:
        # Change service owner
        service = await self.db.get(Service, service_id)
        assert service
        service.owner_id = new_owner or uuid4()
        self.db.add(service)
        await self.db.flush()
        return service.owner_id
