from fastapi import APIRouter, UploadFile, status, Depends

from ..models.util import Id
from ..services.products import ProductsService
from .responses.image import (
    IMAGE_EXISTS_ERROR,
    INVALID_IMAGE_ERROR,
    NOT_FOUND_ERROR,
)
from .responses.products import PRODUCT_NOT_FOUND_ERROR
from .util import get_exception_docs, get_image

router = APIRouter(prefix="/stores/{store_id}/products/{product_id}/image", tags=["Product images"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=get_exception_docs(IMAGE_EXISTS_ERROR, INVALID_IMAGE_ERROR, PRODUCT_NOT_FOUND_ERROR),
)
async def create_product_image(
    store_id: Id,
    product_id: Id,
    image: UploadFile = Depends(get_image),
    service: ProductsService = Depends(ProductsService),
) -> None:
    await service.create_product_image(store_id, product_id, image)


@router.put(
    "",
    responses=get_exception_docs(INVALID_IMAGE_ERROR, PRODUCT_NOT_FOUND_ERROR),
)
async def set_product_image(
    store_id: Id,
    product_id: Id,
    image: UploadFile = Depends(get_image),
    service: ProductsService = Depends(ProductsService),
) -> None:
    await service.set_product_image(store_id, product_id, image)


@router.delete(
    "", status_code=status.HTTP_204_NO_CONTENT, responses=get_exception_docs(NOT_FOUND_ERROR)
)
async def delete_product_image(
    store_id: Id, product_id: Id, service: ProductsService = Depends(ProductsService)
) -> None:
    await service.delete_product_image(store_id, product_id)
