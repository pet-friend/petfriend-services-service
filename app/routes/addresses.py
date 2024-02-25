from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.services.addresses import AddressesService
from app.exceptions.addresses import AddressNotFound
from app.models.addresses import AddressRead, AddressCreate, AddressReadRenamed
from app.models.util import Id
from .responses.addresses import (
    ADDRESS_NOT_FOUND_ERROR,
    ADDRESS_EXISTS_ERROR,
    NON_EXISTENT_ADDRESS_ERROR,
    SERVICE_NOT_FOUND_ERROR,
)
from .util import get_exception_docs

router = APIRouter(
    tags=["Addresses"],
    # TODO: change to /stores/{service_id}/addresses, the same for other services
    prefix="/addresses/{service_id}",
)


@router.post(
    "",
    status_code=http_status.HTTP_201_CREATED,
    responses=get_exception_docs(
        ADDRESS_EXISTS_ERROR, SERVICE_NOT_FOUND_ERROR, NON_EXISTENT_ADDRESS_ERROR
    ),
    response_model=AddressReadRenamed,
)
async def create_address(
    service_id: Id,
    data: AddressCreate,
    addresses_service: AddressesService = Depends(AddressesService),
) -> AddressRead:
    return await addresses_service.create_address(service_id, data)


@router.get(
    "", responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR), response_model=AddressReadRenamed
)
async def get_service_addresses(
    service_id: Id,
    addresses_service: AddressesService = Depends(AddressesService),
) -> AddressRead:
    return await addresses_service.get_address(service_id)


@router.put(
    "",
    response_model=AddressReadRenamed,
    responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR, NON_EXISTENT_ADDRESS_ERROR),
)
async def update_service_addresses(
    service_id: Id,
    data: AddressCreate,
    addresses_service: AddressesService = Depends(AddressesService),
) -> AddressRead:
    try:
        return await addresses_service.update_address(service_id, data)
    except AddressNotFound:
        return await addresses_service.create_address(service_id, data)


@router.delete(
    "",
    responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_service_addresses(
    service_id: Id,
    addresses_service: AddressesService = Depends(AddressesService),
) -> None:
    await addresses_service.delete_address(service_id)
