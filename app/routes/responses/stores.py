from fastapi import HTTPException, status

STORE_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Store not found",
)
