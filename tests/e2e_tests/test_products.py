from typing import Sequence, Any
from uuid import uuid4

from sqlmodel import select

from app.models.addresses import Address
from app.models.stores import Store, Product
from app.models.util import Coordinates
from tests.factories.store_factories import StoreCreateFactory
from tests.factories.product_factories import ProductCreateFactory

from tests.tests_setup import BaseAPITestCase, GetUserCoordinatesMock


class TestStoresProductsRoute(BaseAPITestCase):
    def setup_method(self) -> None:
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
        r_product = await self.client.get(f"/stores/{store_id}/products/{r_product.json()['id']}")
        response_text: dict[str, Any] = r_product.json()
        product: Product | None = await self.db.get(Product, (store_id, response_text["id"]))

        assert product is not None
        assert product.created_at is not None
        assert product.updated_at is not None
        assert response_text.pop("store_id") == store_id
        response_text.pop("id")
        response_text.pop("image_url")
        response_text.pop("reviews_average_rating")
        assert product._categories is not None
        assert len(response_text.items()) == len(self.product_create_json_data.items())

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
        r_product = await self.client.get(f"/stores/{store_id}/products/{r_product.json()['id']}")
        response_text: dict[str, Any] = r_product.json()
        product: Product | None = await self.db.get(Product, (store_id, response_text["id"]))

        assert product is not None
        assert product.created_at is not None
        assert product.updated_at is not None
        assert response_text.pop("store_id") == store_id
        response_text.pop("id")
        assert len(response_text.items()) >= len(self.product_create_json_data.items())

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
        product_create_json_data_2["name"] = "Another product"

        r_product_1 = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product_1.status_code == 201
        r_product_1 = await self.client.get(
            f"/stores/{store_id}/products/{r_product_1.json()['id']}"
        )
        response_text_1: dict[str, Any] = r_product_1.json()
        product_1: Product | None = await self.db.get(Product, (store_id, response_text_1["id"]))
        r_product_2 = await self.client.post(
            f"/stores/{store_id}/products", json=product_create_json_data_2
        )
        assert r_product_2.status_code == 201
        r_product_2 = await self.client.get(
            f"/stores/{store_id}/products/{r_product_2.json()['id']}"
        )
        response_text_2: dict[str, Any] = r_product_2.json()
        product_2: Product | None = await self.db.get(Product, (store_id, response_text_2["id"]))

        assert product_1 is not None
        assert response_text_1.pop("store_id") == store_id
        response_text_1.pop("id")
        response_text_1.pop("image_url")
        response_text_1.pop("reviews_average_rating")
        assert len(response_text_1.items()) == len(self.product_create_json_data.items())
        assert product_2 is not None
        assert response_text_2.pop("store_id") == store_id
        response_text_2.pop("id")
        response_text_2.pop("image_url")
        response_text_2.pop("reviews_average_rating")
        assert len(response_text_2.items()) == len(product_create_json_data_2.items())

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
        response_text.pop("reviews_average_rating")
        assert len(response_text.items()) == len(self.product_create_json_data.items())

    async def test_create_and_modify_product(self) -> None:
        r_store = await self.client.post("/stores", json=self.store_create_json_data)
        assert r_store.status_code == 201
        store_id = r_store.json()["id"]
        self.product_create_json_data["description"] = "Old description"

        r_product = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_product.status_code == 201
        r_product = await self.client.get(f"/stores/{store_id}/products/{r_product.json()['id']}")
        response_text: dict[str, Any] = r_product.json()
        response_text["description"] = "New description :D"
        r_product_2 = await self.client.put(
            f"/stores/{store_id}/products/{response_text['id']}", json=response_text
        )
        r_product_2 = await self.client.get(f"/stores/{store_id}/products/{r_product.json()['id']}")

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

    async def test_delete_product_not_owner_is_forbidden(self) -> None:
        response = await self.client.post("/stores", json=self.store_create_json_data)
        assert response.status_code == 201
        store_id = response.json()["id"]

        r_post = await self.client.post(
            f"/stores/{store_id}/products", json=self.product_create_json_data
        )
        assert r_post.status_code == 201
        product_id = r_post.json()["id"]

        # Change store owner
        store = await self.db.get(Store, store_id)
        assert store
        store.owner_id = uuid4()
        self.db.add(store)
        await self.db.flush()

        response2 = await self.client.delete(f"/stores/{store_id}/products/{product_id}")
        assert response2.status_code == 403

    async def test_get_nearby_products(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        store_base = self.store_create_json_data
        store_base.pop("delivery_range_km")
        store_base["owner_id"] = self.user_id
        addr_base: Any = store_base.pop("address")

        product_base = self.product_create_json_data
        product_base.pop("name")

        # Tienda 1: a menos de 500m del obelisco, radio de 1km -> debería aparecer
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        product_1 = Product(**product_base, name="Producto 1")
        store_base["name"] = "Tienda 1"
        store_1 = Store(**store_base, address=address_1, delivery_range_km=1, products=[product_1])

        # Tienda 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        product_2 = Product(**product_base, name="Producto 2")
        store_base["name"] = "Tienda 2"
        store_2 = Store(**store_base, address=address_2, delivery_range_km=3, products=[product_2])

        # Tienda 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        product_3 = Product(**product_base, name="Producto 3")
        store_base["name"] = "Tienda 3"
        store_3 = Store(**store_base, address=address_3, delivery_range_km=4, products=[product_3])

        self.db.add(store_1)
        self.db.add(store_2)
        self.db.add(store_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/stores/nearby/products", params={"user_address_id": str(address_id)}
        )
        assert response.status_code == 200
        products = response.json()["products"]
        assert {s["name"] for s in products} == {product_1.name, product_3.name}

    async def test_get_nearby_products_name_filter(
        self, mock_get_user_coordinates: GetUserCoordinatesMock
    ) -> None:
        store_base = self.store_create_json_data
        store_base.pop("delivery_range_km")
        store_base["owner_id"] = self.user_id
        addr_base: Any = store_base.pop("address")

        product_base = self.product_create_json_data
        product_base.pop("name")

        # Tienda 1: a menos de 500m del obelisco, radio de 1km -> filtrada por nombre
        address_1 = Address(**addr_base, latitude=-34.60381182712754, longitude=-58.38586757264521)
        product_1 = Product(**product_base, name="Producto AAA")
        store_base["name"] = "Tienda 1"
        store_1 = Store(**store_base, address=address_1, delivery_range_km=1, products=[product_1])

        # Tienda 2: a ~3.8km del obelisco, radio de 3km -> no debería aparecer
        address_2 = Address(**addr_base, latitude=-34.58802836958609, longitude=-58.41891467656516)
        product_2 = Product(**product_base, name="Producto BBB")
        store_base["name"] = "Tienda 2"
        store_2 = Store(**store_base, address=address_2, delivery_range_km=3, products=[product_2])

        # Tienda 3: a ~3.4km del obelisco, radio de 4km -> debería aparecer
        address_3 = Address(**addr_base, latitude=-34.61434525255158, longitude=-58.4172589555573)
        product_3 = Product(**product_base, name="Producto BBB")
        store_base["name"] = "Tienda 3"
        store_3 = Store(**store_base, address=address_3, delivery_range_km=4, products=[product_3])

        self.db.add(store_1)
        self.db.add(store_2)
        self.db.add(store_3)
        await self.db.flush()

        address_id = uuid4()
        mock_get_user_coordinates(
            address_id,
            # obelisco
            return_value=Coordinates(latitude=-34.60360640938748, longitude=-58.38153821730145),
        )

        response = await self.client.get(
            "/stores/nearby/products", params={"user_address_id": str(address_id), "name": "BBB"}
        )
        assert response.status_code == 200
        products = response.json()["products"]
        assert {s["name"] for s in products} == {product_3.name}
