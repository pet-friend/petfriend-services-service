from fastapi import HTTPException, status

PRODUCT_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Product not found",
)

PRODUCT_EXISTS_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A product with this name already exists",
)

# This error is not actually used in the code, it's just for route documentation.
# We can't use both STORE_NOT_FOUND_ERROR and PRODUCT_NOT_FOUND_ERROR for 404s in the docs.
NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "Store or product not found")
