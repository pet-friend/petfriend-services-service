from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.models.services import ServicePublic, ServiceCreate, ServiceRead, ServiceCategory
from app.models.util import Id
from app.serializers.services import ServiceList
from app.services.services import ServicesService
from app.auth import get_caller_id, get_caller_token
from ..responses.addresses import NON_EXISTENT_ADDRESS_ERROR, ADDRESS_NOT_FOUND_ERROR
from ..responses.services import SERVICE_NOT_FOUND_ERROR
from ..responses.auth import FORBIDDEN
from ..util import get_exception_docs


router = APIRouter(prefix="/services", tags=["Services"])


@router.post(
    "",
    response_model=ServiceRead,
    status_code=http_status.HTTP_201_CREATED,
    responses=get_exception_docs(NON_EXISTENT_ADDRESS_ERROR),
)
async def create_service(
    data: ServiceCreate,
    services_service: ServicesService = Depends(ServicesService),
    owner_id: Id = Depends(get_caller_id),
) -> ServicePublic:
    return await services_service.create_service(data, owner_id)


@router.get("")
async def get_services(
    owner_id: Id | None = None,
    name: str | None = Query(None),
    category: ServiceCategory | None = Query(None),
    is_home_service: bool | None = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    services_service: ServicesService = Depends(ServicesService),
) -> ServiceList:
    query = {
        "name": name,
        "owner_id": owner_id,
        "category": category,
        "is_home_service": is_home_service,
    }
    services = await services_service.get_services(limit, offset, **query)
    services_amount = await services_service.count_services(**query)
    return ServiceList(
        services=await services_service.get_services_read(*services), amount=services_amount
    )


@router.get("/me")
async def get_my_services(
    name: str | None = Query(None),
    category: ServiceCategory | None = Query(None),
    is_home_service: bool | None = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    services_service: ServicesService = Depends(ServicesService),
    owner_id: Id = Depends(get_caller_id),
) -> ServiceList:
    query = {
        "name": name,
        "owner_id": owner_id,
        "category": category,
        "is_home_service": is_home_service,
    }
    services = await services_service.get_services(limit, offset, **query)
    services_amount = await services_service.count_services(**query)
    return ServiceList(
        services=await services_service.get_services_read(*services), amount=services_amount
    )


@router.get("/nearby", responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR))
async def get_nearby_services(
    user_address_id: Id,
    name: str | None = Query(None),
    category: ServiceCategory | None = Query(None),
    is_home_service: bool | None = Query(None),
    user_token: str = Depends(get_caller_token),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    services_service: ServicesService = Depends(ServicesService),
    user_id: Id = Depends(get_caller_id),
) -> ServiceList:
    services, services_amount = await services_service.get_nearby_services(
        user_token,
        limit,
        offset,
        user_id,
        user_address_id,
        name=name,
        category=category,
        is_home_service=is_home_service,
    )
    return ServiceList(
        services=await services_service.get_services_read(*services), amount=services_amount
    )


@router.get("/{service_id}", responses=get_exception_docs(SERVICE_NOT_FOUND_ERROR))
async def get_service(
    service_id: str, services_service: ServicesService = Depends(ServicesService)
) -> ServiceRead:
    service = await services_service.get_service_by_id(service_id)
    return (await services_service.get_services_read(service))[0]


@router.put("/{service_id}", responses=get_exception_docs(NON_EXISTENT_ADDRESS_ERROR, FORBIDDEN))
async def update_user_service(
    service_id: Id,
    data: ServiceCreate,
    services_service: ServicesService = Depends(ServicesService),
    user_id: Id = Depends(get_caller_id),
) -> ServiceRead:
    service = await services_service.update_service(service_id, data, user_id)
    return (await services_service.get_services_read(service))[0]


@router.delete(
    "/{service_id}",
    responses=get_exception_docs(SERVICE_NOT_FOUND_ERROR, FORBIDDEN),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_user_service(
    service_id: Id,
    services_service: ServicesService = Depends(ServicesService),
    user_id: Id = Depends(get_caller_id),
) -> None:
    await services_service.delete_service(service_id, user_id)
