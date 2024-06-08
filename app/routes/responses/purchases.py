from fastapi import HTTPException, status

from app.exceptions.products import ProductOutOfStock
from app.exceptions.purchases import PurchaseNotFound

PURCHASE_NOT_FOUND_ERROR = (
    PurchaseNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Purchase not found",
    ),
)

OUT_OF_STOCK = (
    ProductOutOfStock,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't purchase more than the available stock",
    ),
)
