from fastapi import APIRouter, UploadFile, status, Depends

from ..models.util import Id
from ..services.stores import StoresService
from .responses.image import (
    IMAGE_EXISTS_ERROR,
    INVALID_IMAGE_ERROR,
    NOT_FOUND_ERROR,
)
from .responses.stores import STORE_NOT_FOUND_ERROR
from .util import get_exception_docs, get_image

router = APIRouter(prefix="/stores/{store_id}/image", tags=["Store images"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=get_exception_docs(IMAGE_EXISTS_ERROR, INVALID_IMAGE_ERROR, STORE_NOT_FOUND_ERROR),
)
async def create_store_image(
    store_id: Id,
    image: UploadFile = Depends(get_image),
    service: StoresService = Depends(StoresService),
) -> None:
    await service.create_store_image(store_id, image)


@router.put(
    "",
    responses=get_exception_docs(INVALID_IMAGE_ERROR, STORE_NOT_FOUND_ERROR),
)
async def set_store_image(
    store_id: Id,
    image: UploadFile = Depends(get_image),
    service: StoresService = Depends(StoresService),
) -> None:
    await service.set_store_image(store_id, image)


@router.delete(
    "", status_code=status.HTTP_204_NO_CONTENT, responses=get_exception_docs(NOT_FOUND_ERROR)
)
async def delete_store_image(store_id: Id, service: StoresService = Depends(StoresService)) -> None:
    await service.delete_store_image(store_id)
