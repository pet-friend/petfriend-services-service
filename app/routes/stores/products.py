from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from pydantic import BeforeValidator

from app.auth import get_caller_id, get_caller_token
from app.serializers.stores import ProductsList
from app.services.stores import ProductsService
from app.models.stores import Category, Product, ProductCreate, ProductRead
from app.models.util import Id
from ..responses.addresses import ADDRESS_NOT_FOUND_ERROR
from ..responses.stores import STORE_NOT_FOUND_ERROR
from ..responses.products import PRODUCT_EXISTS_ERROR, PRODUCT_NOT_FOUND_ERROR
from ..responses.auth import FORBIDDEN
from ..util import get_exception_docs, process_list

router = APIRouter(tags=["Products"], prefix="/stores")


@router.post(
    "/{store_id}/products",
    status_code=http_status.HTTP_201_CREATED,
    responses=get_exception_docs(STORE_NOT_FOUND_ERROR, PRODUCT_EXISTS_ERROR, FORBIDDEN),
    response_model=ProductRead,
)
async def create_product(
    store_id: Id,
    data: ProductCreate,
    products_service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> Product:
    return await products_service.create_product(store_id, data, user_id)


@router.get("/nearby/products", responses=get_exception_docs(ADDRESS_NOT_FOUND_ERROR))
async def get_nearby_products(
    user_address_id: Id,
    user_token: str = Depends(get_caller_token),
    name: str | None = Query(None),
    categories: Annotated[list[Category], BeforeValidator(process_list)] = Query([]),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    store_service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> ProductsList:
    products, products_amount = await store_service.get_nearby_products(
        user_token, limit, offset, user_id, user_address_id, categories, name=name
    )
    return ProductsList(
        products=await store_service.get_products_read(*products), amount=products_amount
    )


@router.get("/{store_id}/products", responses=get_exception_docs(STORE_NOT_FOUND_ERROR))
async def get_store_products(
    store_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> Sequence[ProductRead]:
    products = await products_service.get_store_products(store_id)
    return await products_service.get_products_read(*products)


@router.get(
    "/{store_id}/products/{product_id}", responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR)
)
async def get_product(
    store_id: Id,
    product_id: Id,
    products_service: ProductsService = Depends(ProductsService),
) -> ProductRead:
    product = await products_service.get_product(store_id, product_id)
    return (await products_service.get_products_read(product))[0]


@router.put(
    "/{store_id}/products/{product_id}",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR, FORBIDDEN),
)
async def update_store_product(
    store_id: Id,
    product_id: Id,
    data: ProductCreate,
    products_service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> ProductRead:
    product = await products_service.update_product(store_id, product_id, data, user_id)
    return (await products_service.get_products_read(product))[0]


@router.delete(
    "/{store_id}/products/{product_id}",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR, FORBIDDEN),
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_store_products(
    store_id: Id,
    product_id: Id,
    products_service: ProductsService = Depends(ProductsService),
    user_id: Id = Depends(get_caller_id),
) -> None:
    await products_service.delete_product(store_id, product_id, user_id)
