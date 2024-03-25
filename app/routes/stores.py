from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.models.stores import StoreCreate, StorePublic, StoreRead
from app.models.util import Id
from app.serializers.stores import StoreList
from app.services.stores import StoresService
from app.auth import get_caller_id, get_caller_token
from .responses.addresses import NON_EXISTENT_ADDRESS_ERROR, ADDRESS_NOT_FOUND_ERROR
from .responses.stores import STORE_NOT_FOUND_ERROR
from .responses.auth import FORBIDDEN
from .util import get_exception_docs


router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post(
    "",
    response_model=StoreRead,
    status_code=http_status.HTTP_201_CREATED,
    responses=get_exception_docs(NON_EXISTENT_ADDRESS_ERROR),
)
async def create_store(
    data: StoreCreate,
    store_service: StoresService = Depends(StoresService),
    owner_id: Id = Depends(get_caller_id),
) -> StorePublic:
    return await store_service.create_store(data, owner_id)


@router.get("")
async def get_stores(
    owner_id: Id | None = None,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
) -> StoreList:
    stores = await store_service.get_stores(limit, offset, owner_id=owner_id)
    stores_amount = await store_service.count_stores(owner_id=owner_id)
    return StoreList(stores=await store_service.get_stores_read(stores), amount=stores_amount)


@router.get("/me")
async def get_my_stores(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
    owner_id: Id = Depends(get_caller_id),
) -> StoreList:
    stores = await store_service.get_stores(limit, offset, owner_id=owner_id)
    stores_amount = await store_service.count_stores(owner_id=owner_id)
    return StoreList(stores=await store_service.get_stores_read(stores), amount=stores_amount)


@router.get("/nearby", responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR))
async def get_nearby_stores(
    user_address_id: Id,
    user_token: str = Depends(get_caller_token),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
    user_id: Id = Depends(get_caller_id),
) -> StoreList:
    stores, stores_amount = await store_service.get_nearby_stores(
        user_token, limit, offset, user_id, user_address_id
    )
    return StoreList(stores=await store_service.get_stores_read(stores), amount=stores_amount)


@router.get("/{store_id}", responses=get_exception_docs(STORE_NOT_FOUND_ERROR))
async def get_store(
    store_id: str, store_service: StoresService = Depends(StoresService)
) -> StoreRead:
    store = await store_service.get_store_by_id(store_id)
    return (await store_service.get_stores_read([store]))[0]


@router.put("/{store_id}", responses=get_exception_docs(NON_EXISTENT_ADDRESS_ERROR, FORBIDDEN))
async def update_user_store(
    store_id: Id,
    data: StoreCreate,
    stores_service: StoresService = Depends(StoresService),
    user_id: Id = Depends(get_caller_id),
) -> StoreRead:
    store = await stores_service.update_store(store_id, data, user_id)
    return (await stores_service.get_stores_read([store]))[0]


@router.delete(
    "/{store_id}",
    responses=get_exception_docs(STORE_NOT_FOUND_ERROR, FORBIDDEN),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_user_store(
    store_id: Id,
    stores_service: StoresService = Depends(StoresService),
    user_id: Id = Depends(get_caller_id),
) -> None:
    await stores_service.delete_store(store_id, user_id)
