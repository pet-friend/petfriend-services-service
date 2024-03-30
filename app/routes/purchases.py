from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from pydantic import PositiveInt

from app.auth import get_caller_id, get_caller_token
from app.models.purchases import Purchase, PurchaseRead
from app.models.util import Id
from app.routes.responses.products import PRODUCT_NOT_FOUND_ERROR
from app.routes.util import get_exception_docs
from app.serializers.purchases import PurchaseList
from app.services.purchases import PurchasesService
from app.config import settings

router = APIRouter(prefix="", tags=["Purchases"])


@router.get(
    "/stores/purchases/me",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
    response_model=PurchaseRead,
)
async def get_my_purchases(
    user_id: Id = Depends(get_caller_id),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    purchases_service: PurchasesService = Depends(),
) -> PurchaseList:
    purchases, count = await purchases_service.get_user_purchases(user_id, limit, offset)
    return PurchaseList(purchases=purchases, amount=count)


@router.get(
    "/stores/{store_id}/purchases",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
    response_model=PurchaseRead,
)
async def get_store_purchases(
    store_id: Id,
    user_id: Id = Depends(get_caller_id),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    purchases_service: PurchasesService = Depends(),
) -> PurchaseList:
    purchases, count = await purchases_service.get_store_purchases(user_id, store_id, limit, offset)
    return PurchaseList(purchases=purchases, amount=count)


@router.post(
    "/stores/{store_id}/purchases",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
    response_model=PurchaseRead,
)
async def create_store_purchase(
    store_id: Id,
    ship_to_address_id: Id,
    products_quantities: dict[Id, PositiveInt],
    purchases_service: PurchasesService = Depends(),
    user_id: Id = Depends(get_caller_id),
    token: str = Depends(get_caller_token),
) -> Purchase:
    """Body must be a dictionary with product ids as keys and quantities as values."""
    return await purchases_service.purchase(
        store_id, products_quantities, user_id, ship_to_address_id, token
    )


@router.get(
    "/stores/{store_id}/purchases/{purchase_id}",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
    response_model=PurchaseRead,
)
async def get_store_purchase(
    store_id: Id,
    purchase_id: Id,
    purchases_service: PurchasesService = Depends(),
    user_id: Id = Depends(get_caller_id),
) -> Purchase:
    return await purchases_service.get_purchase(store_id, purchase_id, user_id)


@router.get(
    "/fee",
)
async def get_fee() -> Decimal:
    return settings.FEE_PERCENTAGE
