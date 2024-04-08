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


# only for docs, PRODUCT_NOT_FOUND_ERROR and STORE_NOT_FOUND_ERROR are used
NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Store or product not found",
)

# only for docs, OUTSIDE_DELIVERY_RANGE, CANT_PURCHASE_FROM_OWN_BUSINESS and OUT_OF_STOCK are used
FORBIDDEN_PURCHASE = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail=(
        "Thrown when a purchase is invalid (outside delivery range, purchasing from your own store,"
        " or an out-of-stock item)"
    ),
)


OUT_OF_STOCK = (
    ProductOutOfStock,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't purchase more than the available stock",
    ),
)
