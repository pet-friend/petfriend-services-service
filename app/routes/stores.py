from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.models.stores import StoreCreate, StoreRead, StoreReadWithImage
from app.models.util import Id
from app.routes.responses.stores import STORE_NOT_FOUND_ERROR
from app.serializers.stores import StoreList
from app.services.stores import StoresService
from app.auth import get_caller_id
from .util import get_exception_docs


router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post("", response_model_exclude_none=True, status_code=http_status.HTTP_201_CREATED)
async def create_store(
    data: StoreCreate,
    store_service: StoresService = Depends(StoresService),
    owner_id: Id = Depends(get_caller_id),
) -> StoreRead:
    return await store_service.create_store(data, owner_id)


@router.get("", response_model_exclude_none=True)
async def get_stores(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
) -> StoreList:
    stores = await store_service.get_stores(limit, offset)
    stores_amount = await store_service.count_stores()
    return StoreList(stores=await store_service.get_stores_with_image(stores), amount=stores_amount)


@router.get("/me", response_model_exclude_none=True)
async def get_my_stores(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
    owner_id: Id = Depends(get_caller_id),
) -> StoreList:
    stores = await store_service.get_stores(limit, offset, owner_id=owner_id)
    stores_amount = await store_service.count_stores(owner_id=owner_id)
    return StoreList(stores=await store_service.get_stores_with_image(stores), amount=stores_amount)


@router.get(
    "/{store_id}",
    responses=get_exception_docs(STORE_NOT_FOUND_ERROR),
    response_model_exclude_none=True,
)
async def get_store(
    store_id: str, store_service: StoresService = Depends(StoresService)
) -> StoreReadWithImage:
    store = await store_service.get_store_by_id(store_id)
    return (await store_service.get_stores_with_image([store]))[0]


@router.put("/{store_id}", response_model=StoreRead)
async def update_user_stores(
    store_id: Id,
    data: StoreCreate,
    stores_service: StoresService = Depends(StoresService),
) -> StoreRead:
    return await stores_service.update_store(store_id, data)


@router.delete(
    "/{store_id}",
    responses=get_exception_docs(STORE_NOT_FOUND_ERROR),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_user_stores(
    store_id: Id,
    stores_service: StoresService = Depends(StoresService),
) -> None:
    await stores_service.delete_store(store_id)
