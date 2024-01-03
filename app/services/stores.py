from typing import Sequence, Any

from fastapi import Depends

# from app.exceptions.stores import StoreNotFoundException
from app.models.stores import StoreCreate, Store
from app.repositories.stores import StoresRepository


class StoresService:
    def __init__(self, stores_repo: StoresRepository = Depends(StoresRepository)):
        self.stores_repo = stores_repo

    async def create_store(self, data: StoreCreate) -> Store:
        store = await self.stores_repo.create(data)
        return store

    async def get_stores(self, limit: int, offset: int, **filters: Any) -> Sequence[Store]:
        stores = await self.stores_repo.get_all(skip=offset, limit=limit, **filters)
        return stores

    async def count_stores(self, **filters: Any) -> int:
        stores_count = await self.stores_repo.count_all(**filters)
        return stores_count

    async def get_store_by_id(self, store_id: str) -> Store | None:
        store = await self.stores_repo.get_by_id(store_id)
        return store
