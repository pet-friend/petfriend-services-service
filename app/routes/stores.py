from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.models.stores import StoreCreate, StoreRead, StoreReadWithImage
from app.routes.responses.stores import STORE_NOT_FOUND_ERROR
from app.validators.error_schema import ErrorSchema
from app.serializers.stores import StoreList
from app.services.stores import StoresService
from .util import get_exception_docs


router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", response_model_exclude_none=True)
async def get_stores(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: StoresService = Depends(StoresService),
) -> StoreList:
    filters = {}  # type: ignore

    stores = await store_service.get_stores(limit, offset, **filters)
    stores_amount = await store_service.count_stores(**filters)
    return StoreList(stores=await store_service.get_stores_with_image(stores), amount=stores_amount)


@router.post(
    "",
    response_model_exclude_none=True,
    status_code=http_status.HTTP_201_CREATED,
    responses={400: {"model": ErrorSchema}},
)
async def create_store(
    data: StoreCreate, store_service: StoresService = Depends(StoresService)
) -> StoreRead:
    return await store_service.create_store(data)


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


# TODO: PUT
# TODO: DELETE
