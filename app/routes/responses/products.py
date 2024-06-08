from fastapi import HTTPException, status

from app.exceptions.products import ProductAlreadyExists, ProductNotFound

PRODUCT_NOT_FOUND_ERROR = (
    ProductNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Product not found",
    ),
)

PRODUCT_EXISTS_ERROR = (
    ProductAlreadyExists,
    HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="A product with this name already exists",
    ),
)
