from typing import Sequence

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.auth import get_caller_id
from app.serializers.products import ProductsList
from app.services.products import ProductsService
from app.models.products import Product, ProductCreate, ProductRead
from app.models.util import Id
from .responses.addresses import ADDRESS_NOT_FOUND_ERROR
from .responses.stores import STORE_NOT_FOUND_ERROR
from .responses.products import PRODUCT_EXISTS_ERROR, PRODUCT_NOT_FOUND_ERROR
from .util import get_exception_docs

router = APIRouter(tags=["Products"], prefix="/stores")


@router.post(
    "/{store_id}/products",
    status_code=http_status.HTTP_201_CREATED,
    responses=get_exception_docs(PRODUCT_EXISTS_ERROR),
    response_model=ProductRead,
)
async def create_product(
    store_id: Id,
    data: ProductCreate,
    products_service: ProductsService = Depends(ProductsService),
) -> Product:
    return await products_service.create_product(store_id, data)


@router.get("/nearby/products", responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR))
async def get_nearby_products(
    user_address_id: Id,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> ProductsList:
    products, products_amount = await store_service.get_nearby_products(
        limit, offset, user_id, user_address_id
    )
    return ProductsList(
        products=await store_service.get_products_read(products), amount=products_amount
    )


@router.get("/{store_id}/products", responses=get_exception_docs(STORE_NOT_FOUND_ERROR))
async def get_store_products(
    store_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> Sequence[ProductRead]:
    products = await products_service.get_store_products(store_id)
    return await products_service.get_products_read(products)


@router.get(
    "/{store_id}/products/{product_id}", responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR)
)
async def get_product(
    store_id: Id,
    product_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> ProductRead:
    product = await products_service.get_product(store_id, product_id)
    return (await products_service.get_products_read((product,)))[0]


@router.put(
    "/{store_id}/products/{product_id}", responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR)
)
async def update_store_product(
    store_id: Id,
    product_id: Id,
    data: ProductCreate,
    products_service: ProductsService = Depends(ProductsService),
) -> ProductRead:
    product = await products_service.update_product(store_id, product_id, data)
    return (await products_service.get_products_read((product,)))[0]


@router.delete(
    "/{store_id}/products/{product_id}",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_store_products(
    store_id: Id,
    product_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> None:
    await products_service.delete_product(store_id, product_id)
