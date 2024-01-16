from typing import Sequence, Any
from uuid import uuid4

from sqlmodel import select

from app.models.products import Product
from tests.factories.store_factories import StoreCreateFactory
from tests.factories.product_factories import ProductCreateFactory

from tests.tests_setup import BaseAPITestCase


class TestStoresRoute(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.store_create_json_data = StoreCreateFactory.build().model_dump(mode="json")
        self.product_create_json_data = ProductCreateFactory.build().model_dump(mode="json")

    async def test_create_product_with_all_fields(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        response_text: dict[str, Any] = r_product.json()
        product: Product | None = await self.db.get(Product, (store_id, response_text["id"]))

        assert product is not None
        assert product.created_at is not None
        assert product.updated_at is not None
        assert response_text.pop("store_id") == store_id
        response_text.pop("id")
        assert response_text == self.product_create_json_data

    async def test_create_product_with_required_fields(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        self.product_create_json_data.pop("description")
        self.product_create_json_data.pop("available")
        self.product_create_json_data.pop("enabled")

        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        response_text: dict[str, Any] = r_product.json()
        product: Product | None = await self.db.get(Product, (store_id, response_text["id"]))

        assert product is not None
        assert product.created_at is not None
        assert product.updated_at is not None
        assert response_text.pop("store_id") == store_id
        response_text.pop("id")
        assert response_text.items() >= self.product_create_json_data.items()

    async def test_create_product_without_some_required_fields(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        self.product_create_json_data.pop("name")

        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 400
        response_text: dict[str, Any] = r_product.json()

        assert response_text == {"detail": {"name": ["Field required"]}}

        products_db: Sequence[Product] = (await self.db.exec(select(Product))).all()
        assert len(products_db) == 0

    async def test_can_create_multiple_products(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        product_create_json_data_2 = ProductCreateFactory.build().model_dump(mode="json")

        r_product_1 = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product_1.status_code == 201
        response_text_1: dict[str, Any] = r_product_1.json()
        product_1: Product | None = await self.db.get(Product, (store_id, response_text_1["id"]))
        r_product_2 = await self.client.post(
            f"/stores/{store_id}/products", json=product_create_json_data_2
        )
        assert r_product_2.status_code == 201
        response_text_2: dict[str, Any] = r_product_2.json()
        product_2: Product | None = await self.db.get(Product, (store_id, response_text_2["id"]))

        assert product_1 is not None
        assert response_text_1.pop("store_id") == store_id
        response_text_1.pop("id")
        assert response_text_1 == self.product_create_json_data
        assert product_2 is not None
        assert response_text_2.pop("store_id") == store_id
        response_text_2.pop("id")
        assert response_text_2 == product_create_json_data_2

    async def test_create_and_get(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]

        r_post = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_post.status_code == 201
        r_get = await self.client.get(f"/stores/{store_id}/products")
        assert r_get.status_code == 200
        response_text: dict[str, Any] = r_get.json()[0]

        assert response_text.pop("store_id") == store_id
        response_text.pop("id")
        response_text.pop("image_url")
        assert response_text.items() == self.product_create_json_data.items()

    async def test_create_and_modify_product(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        self.product_create_json_data["description"] = "Old description"

        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        response_text: dict[str, Any] = r_product.json()
        response_text["description"] = "New description :D"
        r_product_2 = await self.client.put(
            f"/stores/{store_id}/products/{response_text["id"]}", json=response_text
        )

        assert r_product_2.status_code == 200
        response_text_2: dict[str, Any] = r_product_2.json()
        assert response_text_2 == response_text

    async def test_create_delete_get_product_returns_404(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]

        r_post = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_post.status_code == 201
        product_id = r_post.json()["id"]

        r_delete = await self.client.delete(f"/stores/{store_id}/products/{product_id}")
        assert r_delete.status_code == 204

        r_get = await self.client.get(f"/stores/{store_id}/products/{product_id}")
        assert r_get.status_code == 404

    async def test_delete_product_not_exists_returns_404(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]

        r_delete = await self.client.delete(f"/stores/{store_id}/products/{store_id}")
        assert r_delete.status_code == 404

    async def test_delete_store_not_exists_returns_404(self) -> None:
        store_id = uuid4()
        r_delete = await self.client.delete(f"/stores/{store_id}/products/{store_id}")
        assert r_delete.status_code == 404
