import json
from uuid import uuid4

from httpx import AsyncClient

from app.models.stores import StoreRead
from tests.factories.store_factories import StoreCreateFactory
from tests.tests_setup import BaseAPITestCase

with open("tests/assets/test_image.jpg", "rb") as f:
    IMAGE = ("image.jpg", f.read(), "image/jpeg")

with open("tests/assets/test_image_2.jpg", "rb") as f:
    IMAGE_2 = ("image.jpg", f.read(), "image/jpeg")


class TestStoresRoute(BaseAPITestCase):
    def setup_method(self) -> None:
        self.store_create_json_data = StoreCreateFactory.build().model_dump(mode="json")

    async def test_post_should_get_image_url(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201

        store_id = json.loads(r_store.text)["id"]
        r_image = await self.client.post(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]

        r_store_get = await self.client.get(f"/stores/{store_id}")
        assert r_store_get.status_code == 200
        store = StoreRead.model_validate_json(r_store_get.text)
        assert store.image_url is not None

        async with AsyncClient() as client:
            r_image_get = await client.get(store.image_url)
        assert r_image_get.status_code == 200
        assert r_image_get.content == IMAGE[1]

    async def test_post_delete_should_not_get_image_url(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = json.loads(r_store.text)["id"]
        r_image = await self.client.post(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]

        r_image_del = await self.client.delete(f"/stores/{store_id}/image")
        assert r_image_del.status_code == 204

        r_store_get = await self.client.get(f"/stores/{store_id}")
        assert r_store_get.status_code == 200
        store = StoreRead.model_validate_json(r_store_get.text)
        assert store.image_url is None

    async def test_post_put_should_get_second_image(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201

        store_id = json.loads(r_store.text)["id"]
        r_image = await self.client.post(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]

        r_image = await self.client.put(f"/stores/{store_id}/image", files={"image": IMAGE_2})
        assert r_image.status_code == 200
        assert r_image.json()["image_url"]

        r_store_get = await self.client.get(f"/stores/{store_id}")
        assert r_store_get.status_code == 200
        store = StoreRead.model_validate_json(r_store_get.text)
        assert store.image_url is not None

        async with AsyncClient() as client:
            r_image_get = await client.get(store.image_url)
        assert r_image_get.status_code == 200
        assert r_image_get.content == IMAGE_2[1]

    async def test_put_can_create_images(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201

        store_id = json.loads(r_store.text)["id"]
        r_image = await self.client.put(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 200
        assert r_image.json()["image_url"]

        r_store_get = await self.client.get(f"/stores/{store_id}")
        assert r_store_get.status_code == 200
        store = StoreRead.model_validate_json(r_store_get.text)
        assert store.image_url is not None

    async def test_store_starts_without_image(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201

        store_id = json.loads(r_store.text)["id"]

        r_store_get = await self.client.get(f"/stores/{store_id}")
        assert r_store_get.status_code == 200
        store = StoreRead.model_validate_json(r_store_get.text)
        assert store.image_url is None

    async def test_post_image_no_store_should_return_404(self) -> None:
        store_id = uuid4()
        r_image = await self.client.post(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 404

    async def test_put_image_no_store_should_return_404(self) -> None:
        store_id = uuid4()
        r_image = await self.client.put(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 404

    async def test_delete_image_no_store_should_return_404(self) -> None:
        store_id = uuid4()
        r_image = await self.client.delete(f"/stores/{store_id}/image")
        assert r_image.status_code == 404

    async def test_delete_no_image_should_return_404(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201

        store_id = json.loads(r_store.text)["id"]
        r_image = await self.client.delete(f"/stores/{store_id}/image")
        assert r_image.status_code == 404

    async def test_cant_post_twice(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201

        store_id = json.loads(r_store.text)["id"]
        r_image = await self.client.post(f"/stores/{store_id}/image", files={"image": IMAGE})
        assert r_image.status_code == 201
        assert r_image.json()["image_url"]
        r_image = await self.client.post(f"/stores/{store_id}/image", files={"image": IMAGE_2})
        assert r_image.status_code == 409
