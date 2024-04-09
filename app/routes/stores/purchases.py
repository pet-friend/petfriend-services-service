from fastapi import APIRouter, Depends, Query, status
from pydantic import PositiveInt

from app.auth import get_caller_id, get_caller_token
from app.models.stores import Purchase, PurchaseRead
from app.models.util import Id
from app.routes.util import get_exception_docs
from app.serializers.stores import PurchaseList
from app.services.stores import PurchasesService
from ..responses.stores import STORE_NOT_FOUND_ERROR
from ..responses.products import PRODUCT_NOT_FOUND_ERROR
from ..responses.purchases import OUT_OF_STOCK, PURCHASE_NOT_FOUND_ERROR
from ..responses.payments import (
    CANT_BUY_FROM_OWN_BUSINESS,
    COLLECTOR_NOT_READY,
    OUTSIDE_BUSINESS_RANGE,
)
from ..responses.auth import FORBIDDEN

router = APIRouter(prefix="", tags=["Purchases"])


@router.post(
    "/stores/{store_id}/purchases",
    responses=get_exception_docs(
        STORE_NOT_FOUND_ERROR,
        PRODUCT_NOT_FOUND_ERROR,
        OUTSIDE_BUSINESS_RANGE,
        CANT_BUY_FROM_OWN_BUSINESS,
        OUT_OF_STOCK,
        COLLECTOR_NOT_READY,
    ),
    response_model=PurchaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_store_purchase(
    store_id: Id,
    delivery_address_id: Id,
    products_quantities: dict[Id, PositiveInt],
    purchases_service: PurchasesService = Depends(),
    user_id: Id = Depends(get_caller_id),
    token: str = Depends(get_caller_token),
) -> Purchase:
    """Body must be a dictionary with product ids as keys and quantities as values."""
    return await purchases_service.purchase(
        store_id, products_quantities, user_id, delivery_address_id, token
    )


@router.get("/stores/purchases/me")
async def get_my_purchases(
    user_id: Id = Depends(get_caller_id),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    purchases_service: PurchasesService = Depends(),
) -> PurchaseList:
    purchases, count = await purchases_service.get_user_purchases(user_id, limit, offset)
    return PurchaseList(purchases=purchases_service.get_purchases_read(*purchases), amount=count)


@router.get("/stores/{store_id}/purchases", responses=get_exception_docs(FORBIDDEN))
async def get_store_purchases(
    store_id: Id,
    user_id: Id = Depends(get_caller_id),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    purchases_service: PurchasesService = Depends(),
) -> PurchaseList:
    purchases, count = await purchases_service.get_store_purchases(store_id, user_id, limit, offset)
    return PurchaseList(purchases=purchases_service.get_purchases_read(*purchases), amount=count)


@router.get(
    "/stores/{store_id}/purchases/{purchase_id}",
    responses=get_exception_docs(FORBIDDEN, PURCHASE_NOT_FOUND_ERROR),
    response_model=PurchaseRead,
)
async def get_store_purchase(
    store_id: Id,
    purchase_id: Id,
    purchases_service: PurchasesService = Depends(),
    user_id: Id = Depends(get_caller_id),
) -> Purchase:
    return await purchases_service.get_purchase(store_id, purchase_id, user_id)
