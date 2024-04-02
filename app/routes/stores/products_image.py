from fastapi import APIRouter, UploadFile, status, Depends

from app.auth import get_caller_id

from app.models.util import Id, ImageUrlModel
from app.services.stores import ProductsService
from ..responses.image import (
    IMAGE_EXISTS_ERROR,
    INVALID_IMAGE_ERROR,
    NOT_FOUND_ERROR,
)
from ..responses.products import PRODUCT_NOT_FOUND_ERROR
from ..responses.auth import FORBIDDEN
from ..util import get_exception_docs, get_image

router = APIRouter(prefix="/stores/{store_id}/products/{product_id}/image", tags=["Product images"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=get_exception_docs(
        IMAGE_EXISTS_ERROR, INVALID_IMAGE_ERROR, PRODUCT_NOT_FOUND_ERROR, FORBIDDEN
    ),
)
async def create_product_image(
    store_id: Id,
    product_id: Id,
    image: UploadFile = Depends(get_image),
    service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> ImageUrlModel:
    url = await service.create_product_image(store_id, product_id, image, user_id)
    return ImageUrlModel(image_url=url)


@router.put(
    "",
    responses=get_exception_docs(INVALID_IMAGE_ERROR, PRODUCT_NOT_FOUND_ERROR, FORBIDDEN),
)
async def set_product_image(
    store_id: Id,
    product_id: Id,
    image: UploadFile = Depends(get_image),
    service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> ImageUrlModel:
    url = await service.set_product_image(store_id, product_id, image, user_id)
    return ImageUrlModel(image_url=url)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=get_exception_docs(NOT_FOUND_ERROR, FORBIDDEN),
)
async def delete_product_image(
    store_id: Id,
    product_id: Id,
    service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> None:
    await service.delete_product_image(store_id, product_id, user_id)
