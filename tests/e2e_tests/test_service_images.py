import json
from uuid import uuid4

from httpx import AsyncClient

from app.models.services import ServiceRead
from tests.factories.service_factories import ServiceCreateFactory
from tests.tests_setup import BaseAPITestCase

with open("tests/assets/test_image.jpg", "rb") as f:
    IMAGE = ("image.jpg", f.read(), "image/jpeg")

with open("tests/assets/test_image_2.jpg", "rb") as f:
    IMAGE_2 = ("image.jpg", f.read(), "image/jpeg")


class TestServicesRoute(BaseAPITestCase):
    def setup_method(self) -> None:
        self.service_create_json_data = ServiceCreateFactory.build().model_dump(mode="json")

    async def test_post_should_get_image_url(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201

        service_id = json.loads(r_service.text)["id"]
        r_image = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]

        r_service_get = await self.client.get(f"/services/{service_id}")
        assert r_service_get.status_code == 200
        service = ServiceRead.model_validate_json(r_service_get.text)
        assert service.image_url is not None

        async with AsyncClient() as client:
            r_image_get = await client.get(service.image_url)
        assert r_image_get.status_code == 200
        assert r_image_get.content == IMAGE[1]

    async def test_post_delete_should_not_get_image_url(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]
        r_image = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]

        r_image_del = await self.client.delete(f"/services/{service_id}/image")
        assert r_image_del.status_code == 204

        r_service_get = await self.client.get(f"/services/{service_id}")
        assert r_service_get.status_code == 200
        service = ServiceRead.model_validate_json(r_service_get.text)
        assert service.image_url is None

    async def test_post_put_should_get_second_image(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201

        service_id = json.loads(r_service.text)["id"]
        r_image = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]

        r_image = await self.client.put(f"/services/{service_id}/image", files={"image": IMAGE_2})
        assert r_image.status_code == 200
        assert r_image.json()["image_url"]

        r_service_get = await self.client.get(f"/services/{service_id}")
        assert r_service_get.status_code == 200
        service = ServiceRead.model_validate_json(r_service_get.text)
        assert service.image_url is not None

        async with AsyncClient() as client:
            r_image_get = await client.get(service.image_url)
        assert r_image_get.status_code == 200
        assert r_image_get.content == IMAGE_2[1]

    async def test_put_can_create_images(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201

        service_id = json.loads(r_service.text)["id"]
        r_image = await self.client.put(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 200
        assert r_image.json()["image_url"]

        r_service_get = await self.client.get(f"/services/{service_id}")
        assert r_service_get.status_code == 200
        service = ServiceRead.model_validate_json(r_service_get.text)
        assert service.image_url is not None

    async def test_can_post_without_file_extension_and_content_type(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        r_post = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE[1]})
        assert r_post.status_code == 201

    async def test_cant_post_random_bytes(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        r_post = await self.client.post(
            f"/services/{service_id}/image", files={"image": bytes(range(100))}
        )
        assert r_post.status_code == 400

    async def test_can_put_posted_image(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201
        service_id = json.loads(r_service.text)["id"]

        r_post = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_post.status_code == 201
        url = r_post.json()["image_url"]

        async with AsyncClient() as client:
            r_image = await client.get(url)
        assert r_image.status_code == 200

        r_put = await self.client.put(
            f"/services/{service_id}/image", files={"image": r_image.content}
        )
        assert r_put.status_code == 200

    async def test_service_starts_without_image(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201

        service_id = json.loads(r_service.text)["id"]

        r_service_get = await self.client.get(f"/services/{service_id}")
        assert r_service_get.status_code == 200
        service = ServiceRead.model_validate_json(r_service_get.text)
        assert service.image_url is None

    async def test_post_image_no_service_should_return_404(self) -> None:
        service_id = uuid4()
        r_image = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 404

    async def test_put_image_no_service_should_return_404(self) -> None:
        service_id = uuid4()
        r_image = await self.client.put(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 404

    async def test_delete_image_no_service_should_return_404(self) -> None:
        service_id = uuid4()
        r_image = await self.client.delete(f"/services/{service_id}/image")
        assert r_image.status_code == 404

    async def test_delete_no_image_should_return_404(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201

        service_id = json.loads(r_service.text)["id"]
        r_image = await self.client.delete(f"/services/{service_id}/image")
        assert r_image.status_code == 404

    async def test_cant_post_twice(self) -> None:
        r_service = await self.client.post("/services", json=self.service_create_json_data)
        assert r_service.status_code == 201

        service_id = json.loads(r_service.text)["id"]
        r_image = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]
        r_image = await self.client.post(f"/services/{service_id}/image", files={"image": IMAGE_2})
        assert r_image.status_code == 409
