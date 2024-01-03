from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from app.models.stores import StoreCreate, StoreRead
from app.routes.responses.stores import STORE_NOT_FOUND_ERROR
from app.serializers.errors import ValidationErrorMessage
from app.serializers.stores import StoreList

from app.services.stores import StoresService


router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", response_model_exclude_none=True)
async def get_stores(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
) -> StoreList:
    # filters = await process_stores_filters(
    #     adopted, type, breed, colour, gender, owner, shelter, size, age
    # )
    filters = {}  # type: ignore

    stores = await store_service.get_stores(limit, offset, **filters)
    stores_amount = await store_service.count_stores(**filters)
    return StoreList(stores=stores, amount=stores_amount)


@router.post(
    "",
    response_model_exclude_none=True,
    status_code=http_status.HTTP_201_CREATED,
    responses={400: {"model": ValidationErrorMessage}},
)
async def create_store(
    data: StoreCreate, store_service: StoresService = Depends(StoresService)
) -> StoreRead:
    return await store_service.create_store(data)


@router.get("/{store_id}", response_model_exclude_none=True)
async def get_store(
    store_id: str, store_service: StoresService = Depends(StoresService)
) -> StoreRead:
    store = await store_service.get_store_by_id(store_id)
    if store is None:
        raise STORE_NOT_FOUND_ERROR
    return store
