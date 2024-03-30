from fastapi import HTTPException, status

from app.exceptions.stores import StoreAlreadyExists, StoreNotFound

STORE_NOT_FOUND_ERROR = (
    StoreNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Store not found",
    ),
)

STORE_EXISTS_ERROR = (
    StoreAlreadyExists,
    HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="A store with this name already exists",
    ),
)
