from fastapi import APIRouter, UploadFile, status, Depends

from app.auth import get_caller_id

from app.models.util import Id, ImageUrlModel
from app.services.stores import StoresService
from ..responses.image import IMAGE_EXISTS_ERROR, INVALID_IMAGE_ERROR, IMAGE_NOT_FOUND_ERROR
from ..responses.stores import STORE_NOT_FOUND_ERROR
from ..responses.auth import FORBIDDEN
from ..util import get_exception_docs, get_image

router = APIRouter(prefix="/stores/{store_id}/image", tags=["Store images"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=get_exception_docs(
        IMAGE_EXISTS_ERROR, INVALID_IMAGE_ERROR, STORE_NOT_FOUND_ERROR, FORBIDDEN
    ),
)
async def create_store_image(
    store_id: Id,
    image: UploadFile = Depends(get_image),
    service: StoresService = Depends(StoresService),
    user_id: Id = Depends(get_caller_id),
) -> ImageUrlModel:
    url = await service.create_store_image(store_id, image, user_id)
    return ImageUrlModel(image_url=url)


@router.put(
    "",
    responses=get_exception_docs(INVALID_IMAGE_ERROR, STORE_NOT_FOUND_ERROR, FORBIDDEN),
)
async def set_store_image(
    store_id: Id,
    image: UploadFile = Depends(get_image),
    service: StoresService = Depends(StoresService),
    user_id: Id = Depends(get_caller_id),
) -> ImageUrlModel:
    url = await service.set_store_image(store_id, image, user_id)
    return ImageUrlModel(image_url=url)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=get_exception_docs(STORE_NOT_FOUND_ERROR, IMAGE_NOT_FOUND_ERROR, FORBIDDEN),
)
async def delete_store_image(
    store_id: Id,
    service: StoresService = Depends(StoresService),
    user_id: Id = Depends(get_caller_id),
) -> None:
    await service.delete_store_image(store_id, user_id)
