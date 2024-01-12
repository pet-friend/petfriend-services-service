from typing import Sequence, Any

from fastapi import Depends
from app.exceptions.repository import RecordNotFound
from app.exceptions.stores import StoreNotFound


from app.models.stores import StoreCreate, Store, StoreReadWithImage
from app.models.util import File, Id
from app.repositories.stores import StoresRepository
from .files import FilesService, stores_images_service


class StoresService:
    def __init__(
        self,
        stores_repo: StoresRepository = Depends(StoresRepository),
        files_service: FilesService = Depends(stores_images_service),
    ):
        self.stores_repo = stores_repo
        self.files_service = files_service

    async def create_store(self, data: StoreCreate) -> Store:
        store = await self.stores_repo.create(data)
        return store

    async def get_stores(self, limit: int, offset: int, **filters: Any) -> Sequence[Store]:
        stores = await self.stores_repo.get_all(skip=offset, limit=limit, **filters)
        return stores

    async def count_stores(self, **filters: Any) -> int:
        stores_count = await self.stores_repo.count_all(**filters)
        return stores_count

    async def get_store_by_id(self, store_id: str) -> Store:
        store = await self.stores_repo.get_by_id(store_id)
        if store is None:
            raise StoreNotFound
        return store

    async def get_stores_with_image(self, stores: Sequence[Store]) -> Sequence[StoreReadWithImage]:
        result = []
        token = self.files_service.get_token()
        for store in stores:  # TODO: make this concurrent
            image = await self.files_service.get_file_url(store.id, token)
            result.append(StoreReadWithImage(**store.model_dump(), image_url=image))
        return result

    async def update_store(self, service_id: Id, data: StoreCreate) -> Store:
        try:
            return await self.stores_repo.update(service_id, data.model_dump())
        except RecordNotFound as e:
            raise StoreNotFound from e

    async def delete_store(self, service_id: Id) -> None:
        try:
            await self.files_service.delete_file(service_id)  # delete image if exists
        except FileNotFoundError:
            pass
        try:
            await self.stores_repo.delete(service_id)
        except RecordNotFound as e:
            raise StoreNotFound from e

    async def create_store_image(self, store_id: Id, image: File) -> None:
        # assert store exists
        await self.get_store_by_id(store_id)  # type: ignore
        await self.files_service.create_file(store_id, image)

    async def set_store_image(self, store_id: Id, image: File) -> None:
        await self.get_store_by_id(store_id)  # type: ignore
        await self.files_service.set_file(store_id, image)

    async def delete_store_image(self, store_id: Id) -> None:
        await self.get_store_by_id(store_id)  # type: ignore
        await self.files_service.delete_file(store_id)
