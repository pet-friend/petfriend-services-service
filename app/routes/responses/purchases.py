from fastapi import HTTPException, status

from app.exceptions.products import ProductOutOfStock
from app.exceptions.purchases import (
    PurchaseNotFound,
    StoreNotReady,
    OutsideDeliveryRange,
    CantPurchaseFromOwnStore,
)

PURCHASE_NOT_FOUND_ERROR = (
    PurchaseNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Purchase not found",
    ),
)

STORE_NOT_READY = (
    StoreNotReady,
    HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The store owner has not linked his payment account or an address to the store",
    ),
)

# only for docs, PRODUCT_NOT_FOUND_ERROR and STORE_NOT_FOUND_ERROR are used
NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Store or product not found",
)

# only for docs, OUTSIDE_DELIVERY_RANGE, CANT_PURCHASE_FROM_OWNS_STORE and OUT_OF_STOCK are used
FORBIDDEN_PURCHASE = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail=(
        "Thrown when a purchase is invalid (outside delivery range, purchasing from your own store,"
        " or an out-of-stock item)"
    ),
)


OUTSIDE_DELIVERY_RANGE = (
    OutsideDeliveryRange,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The store does not deliver to this address",
    ),
)

CANT_PURCHASE_FROM_OWNS_STORE = (
    CantPurchaseFromOwnStore,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't purchase from a store you own",
    ),
)

OUT_OF_STOCK = (
    ProductOutOfStock,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't purchase more than the available stock",
    ),
)
