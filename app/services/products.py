# pylint: disable=W0212 # access protected member
import logging
from typing import Any, Iterable, Sequence
from asyncio import gather

from fastapi import Depends
from app.exceptions.users import Forbidden

from app.models.util import File, Id
from app.models.products import Category, ProductCategories, ProductCreate, Product, ProductRead
from app.repositories.products import ProductsRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.products import ProductAlreadyExists, ProductNotFound, ProductOutOfStock
from app.services.files import FilesService, products_images_service
from app.services.stores import StoresService
from app.services.users import UsersService


class ProductsService:
    def __init__(
        self,
        products_repo: ProductsRepository = Depends(ProductsRepository),
        stores_service: StoresService = Depends(StoresService),
        files_service: FilesService = Depends(products_images_service),
        users_service: UsersService = Depends(UsersService),
    ):
        self.products_repo = products_repo
        self.stores_service = stores_service
        self.files_service = files_service
        self.users_service = users_service

    async def create_product(self, store_id: Id, data: ProductCreate, user_id: Id) -> Product:
        store = await self.stores_service.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden
        if await self.products_repo.get_by_name(store_id, data.name) is not None:
            raise ProductAlreadyExists

        # map data.categories to ProductCategories model
        categories = [ProductCategories(category=category) for category in data.categories]
        logging.info(f"Creating product {data.name} in store {store_id} with data {data}")
        product = Product(store_id=store_id, **data.model_dump(), _categories=categories)
        return await self.products_repo.save(product)

    async def get_product(self, store_id: Id, product_id: Id) -> Product:
        product = await self.products_repo.get_by_id((store_id, product_id))
        if product is None:
            raise ProductNotFound

        return product

    async def update_product(
        self, store_id: Id, product_id: Id, data: ProductCreate, user_id: Id
    ) -> Product:
        store = await self.stores_service.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        try:
            categories = [ProductCategories(category=category) for category in data.categories]
            return await self.products_repo.update(
                (store_id, product_id), data.model_dump() | {"_categories": categories}
            )
        except RecordNotFound as e:
            raise ProductNotFound from e

    async def delete_product(self, store_id: Id, product_id: Id, user_id: Id) -> None:
        store = await self.stores_service.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        image_id = self.__get_image_id(store_id, product_id)
        if await self.files_service.file_exists(image_id):
            await self.files_service.delete_file(image_id)
        try:
            await self.products_repo.delete((store_id, product_id))
        except RecordNotFound as e:
            raise ProductNotFound from e

    async def get_store_products(self, store_id: Id) -> Sequence[Product]:
        return await self.products_repo.get_all(store_id=store_id)

    async def get_nearby_products(
        self,
        user_token: str,
        limit: int,
        offset: int,
        user_id: Id,
        user_address_id: Id,
        categories: list[Category] | None = None,
        **filters: Any,
    ) -> tuple[Sequence[Product], int]:
        """
        Returns a tuple of products and the total amount of products nearby
        """
        c = await self.users_service.get_user_address_coordinates(
            user_id, user_address_id, user_token
        )
        products = await self.products_repo.get_nearby(
            c.latitude, c.longitude, skip=offset, limit=limit, categories=categories, **filters
        )
        amount = await self.products_repo.count_nearby(
            c.latitude, c.longitude, categories=categories, **filters
        )
        return products, amount

    async def get_products_read(self, products: Iterable[Product]) -> Sequence[ProductRead]:
        token = self.files_service.get_token()
        return await gather(*(self.__readable(product, token) for product in products))

    async def create_product_image(
        self, store_id: Id, product_id: Id, image: File, user_id: Id
    ) -> str:
        product = await self.get_product(store_id, product_id)
        if product.store.owner_id != user_id:
            raise Forbidden

        return await self.files_service.create_file(
            self.__get_image_id(store_id, product_id), image
        )

    async def set_product_image(
        self, store_id: Id, product_id: Id, image: File, user_id: Id
    ) -> str:
        product = await self.get_product(store_id, product_id)
        if product.store.owner_id != user_id:
            raise Forbidden

        return await self.files_service.set_file(self.__get_image_id(store_id, product_id), image)

    async def delete_product_image(self, store_id: Id, product_id: Id, user_id: Id) -> None:
        product = await self.get_product(store_id, product_id)
        if product.store.owner_id != user_id:
            raise Forbidden

        await self.files_service.delete_file(self.__get_image_id(store_id, product_id))

    async def update_stock(self, product: Product, amount: int) -> None:
        """
        Amount can be a negative number to decrease stock
        Raises ProductOutOfStock if the product would have negative stock
        """
        if product.available is None:
            return
        if product.available + amount < 0:
            raise ProductOutOfStock
        product.available += amount
        await self.products_repo.save(product)

    async def __readable(self, product: Product, token: str) -> ProductRead:
        image = await self.files_service.get_file_url(
            self.__get_image_id(product.store_id, product.id), token
        )
        categories = [category.category for category in product._categories]
        return ProductRead(**product.model_dump(), image_url=image, categories=categories)

    def __get_image_id(self, store_id: Id, product_id: Id) -> str:
        return f"{store_id}-{product_id}"
