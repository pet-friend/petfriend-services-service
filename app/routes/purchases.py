from decimal import Decimal
from fastapi import APIRouter, Depends
from pydantic import PositiveInt

from app.auth import get_caller_token
from app.models.util import Id
from app.routes.responses.products import PRODUCT_NOT_FOUND_ERROR
from app.routes.util import get_exception_docs
from app.services.purchases import PurchasesService
from app.config import settings

router = APIRouter(prefix="", tags=["Purchases"])


@router.post(
    "/stores/{store_id}/purchases",
    responses=get_exception_docs(PRODUCT_NOT_FOUND_ERROR),
)
async def purchase(
    store_id: Id,
    products_quantities: dict[Id, PositiveInt],
    purchases_service: PurchasesService = Depends(),
    token: str = Depends(get_caller_token),
) -> str:
    """Body must be a dictionary with product ids as keys and quantities as values."""
    return await purchases_service.purchase(store_id, products_quantities, token)


@router.get(
    "/fee",
)
async def get_fee() -> Decimal:
    return settings.FEE_PERCENTAGE
