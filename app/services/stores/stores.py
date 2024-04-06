from asyncio import gather
from typing import Sequence, Any

from fastapi import Depends

from app.exceptions.stores import StoreAlreadyExists, StoreNotFound
from app.exceptions.users import Forbidden
from app.models.stores import StoreCreate, Store, StoreRead
from app.models.util import File, Id
from app.repositories.stores import StoresRepository
from ..users import UsersService
from ..addresses import AddressesService
from ..files import FilesService, stores_images_service


class StoresService:
    def __init__(
        self,
        stores_repo: StoresRepository = Depends(StoresRepository),
        files_service: FilesService = Depends(stores_images_service),
        users_service: UsersService = Depends(UsersService),
    ):
        self.stores_repo = stores_repo
        self.files_service = files_service
        self.users_service = users_service

    async def create_store(self, data: StoreCreate, owner_id: Id) -> Store:
        store = await self.stores_repo.get_by_name(data.name)
        if store is not None:
            raise StoreAlreadyExists
        address = await AddressesService.get_address(data.address)
        store = Store(**data.model_dump(exclude={"address"}), owner_id=owner_id, address=address)
        return await self.stores_repo.save(store)

    async def get_stores(self, limit: int, skip: int, **filters: Any) -> Sequence[Store]:
        stores = await self.stores_repo.get_all(skip=skip, limit=limit, **filters)
        return stores

    async def get_nearby_stores(
        self,
        user_token: str,
        limit: int,
        skip: int,
        user_id: Id,
        user_address_id: Id,
        **filters: Any
    ) -> tuple[Sequence[Store], int]:
        """
        Returns a tuple of stores and the total amount of stores nearby
        """
        c = await self.users_service.get_user_address_coordinates(
            user_id, user_address_id, user_token
        )
        stores = await self.stores_repo.get_nearby(
            c.latitude, c.longitude, skip=skip, limit=limit, **filters
        )
        amount = await self.stores_repo.count_nearby(c.latitude, c.longitude, **filters)
        return stores, amount

    async def count_stores(self, **filters: Any) -> int:
        stores_count = await self.stores_repo.count_all(**filters)
        return stores_count

    async def get_store_by_id(self, store_id: Id | str) -> Store:
        store = await self.stores_repo.get_by_id(store_id)
        if store is None:
            raise StoreNotFound
        return store

    async def get_stores_read(self, *stores: Store) -> Sequence[StoreRead]:
        token = self.files_service.get_token()
        return await gather(*(self.__readable(store, token) for store in stores))

    async def update_store(self, store_id: Id, data: StoreCreate, user_id: Id) -> Store:
        store = await self.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        address = await AddressesService.get_address(data.address)
        return await self.stores_repo.update(store_id, {**data.model_dump(), "address": address})

    async def delete_store(self, store_id: Id, user_id: Id) -> None:
        store = await self.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        for product in store.products:
            try:
                await self.files_service.delete_file(product.id)  # delete image if exists
            except FileNotFoundError:
                pass

        try:
            await self.files_service.delete_file(store_id)  # delete image if exists
        except FileNotFoundError:
            pass
        await self.stores_repo.delete(store_id)

    async def create_store_image(self, store_id: Id, image: File, user_id: Id) -> str:
        store = await self.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        return await self.files_service.create_file(store_id, image)

    async def set_store_image(self, store_id: Id, image: File, user_id: Id) -> str:
        store = await self.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        return await self.files_service.set_file(store_id, image)

    async def delete_store_image(self, store_id: Id, user_id: Id) -> None:
        store = await self.get_store_by_id(store_id)
        if store.owner_id != user_id:
            raise Forbidden

        await self.files_service.delete_file(store_id)

    async def __readable(self, store: Store, token: str) -> StoreRead:
        image = await self.files_service.get_file_url(store.id, token)
        return StoreRead(**store.model_dump(), address=store.address, image_url=image)
