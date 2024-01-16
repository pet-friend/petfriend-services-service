from fastapi import HTTPException, status

PRODUCT_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Product not found",
)

PRODUCT_EXISTS_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A product with this name already exists",
)
