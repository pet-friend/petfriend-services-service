from typing import Sequence
from asyncio import gather

from fastapi import Depends

from app.models.util import File, Id
from app.models.products import ProductCreate, Product, ProductReadWithImage
from app.repositories.products import ProductsRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.products import ProductAlreadyExists, ProductNotFound
from app.services.files import FilesService, products_images_service
from app.services.stores import StoresService


class ProductsService:
    def __init__(
        self,
        products_repo: ProductsRepository = Depends(ProductsRepository),
        stores_service: StoresService = Depends(StoresService),
        files_service: FilesService = Depends(products_images_service),
    ):
        self.products_repo = products_repo
        self.stores_service = stores_service
        self.files_service = files_service

    async def create_product(self, store_id: Id, data: ProductCreate) -> Product:
        await self.stores_service.get_store_by_id(store_id)  # assert store exists
        if await self.products_repo.get_by_name(store_id, data.name) is not None:
            raise ProductAlreadyExists
        product = Product(store_id=store_id, **data.model_dump())
        return await self.products_repo.save(product)

    async def get_product(self, store_id: Id, product_id: Id) -> Product:
        product = await self.products_repo.get_by_id((store_id, product_id))
        if product is None:
            raise ProductNotFound
        return product

    async def update_product(self, store_id: Id, product_id: Id, data: ProductCreate) -> Product:
        try:
            return await self.products_repo.update((store_id, product_id), data.model_dump())
        except RecordNotFound as e:
            raise ProductNotFound from e

    async def delete_product(self, store_id: Id, product_id: Id) -> None:
        if await self.files_service.file_exists(self.__image_id(store_id, product_id)):
            await self.delete_product_image(store_id, product_id)
        try:
            await self.products_repo.delete((store_id, product_id))
        except RecordNotFound as e:
            raise ProductNotFound from e

    async def get_store_products(self, store_id: Id) -> Sequence[Product]:
        return await self.products_repo.get_all(store_id=store_id)

    async def get_products_with_image(
        self, products: Sequence[Product]
    ) -> Sequence[ProductReadWithImage]:
        token = self.files_service.get_token()
        return await gather(*(self.__with_image(product, token) for product in products))

    async def create_product_image(self, store_id: Id, product_id: Id, image: File) -> None:
        # assert store exists
        await self.get_product(store_id, product_id)
        await self.files_service.create_file(self.__image_id(store_id, product_id), image)

    async def set_product_image(self, store_id: Id, product_id: Id, image: File) -> None:
        await self.get_product(store_id, product_id)
        await self.files_service.set_file(self.__image_id(store_id, product_id), image)

    async def delete_product_image(self, store_id: Id, product_id: Id) -> None:
        await self.get_product(store_id, product_id)
        await self.files_service.delete_file(self.__image_id(store_id, product_id))

    async def __with_image(self, product: Product, token: str) -> ProductReadWithImage:
        image = await self.files_service.get_file_url(
            self.__image_id(product.store_id, product.id), token
        )
        return ProductReadWithImage(**product.model_dump(), image_url=image)

    def __image_id(self, store_id: Id, product_id: Id) -> str:
        return f"{store_id}-{product_id}"
