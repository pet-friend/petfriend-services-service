from typing import Sequence
from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.services.products import ProductsService
from app.models.products import ProductRead, ProductCreate, ProductReadWithImage
from app.models.util import Id
from .responses.stores import STORE_NOT_FOUND_ERROR
from .responses.products import PRODUCT_EXISTS_ERROR, PRODUCT_NOT_FOUND_ERROR
from .util import get_exception_docs

router = APIRouter(
    tags=["Products"],
    prefix="/stores/{store_id}/products",
)


@router.post(
    "",
    status_code=http_status.HTTP_201_CREATED,
    responses=get_exception_docs(PRODUCT_EXISTS_ERROR),
)
async def create_product(
    store_id: Id,
    data: ProductCreate,
    products_service: ProductsService = Depends(ProductsService),
) -> ProductRead:
    return await products_service.create_product(store_id, data)


@router.get("", responses=get_exception_docs(STORE_NOT_FOUND_ERROR))
async def get_store_products(
    store_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> Sequence[ProductReadWithImage]:
    products = await products_service.get_store_products(store_id)
    return await products_service.get_products_with_image(products)


@router.get("/{product_id}", responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR))
async def get_product(
    store_id: Id,
    product_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> ProductReadWithImage:
    product = await products_service.get_product(store_id, product_id)
    return (await products_service.get_products_with_image((product,)))[0]


@router.put("/{product_id}", responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR))
async def update_store_product(
    store_id: Id,
    product_id: Id,
    data: ProductCreate,
    products_service: ProductsService = Depends(ProductsService),
) -> ProductRead:
    return await products_service.update_product(store_id, product_id, data)


@router.delete(
    "/{product_id}",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_store_products(
    store_id: Id,
    product_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> None:
    await products_service.delete_product(store_id, product_id)
