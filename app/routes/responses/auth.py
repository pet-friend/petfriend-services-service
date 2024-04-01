from fastapi import status, HTTPException

from app.exceptions.users import Forbidden

UNAUTHORIZED = HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid access token")
FORBIDDEN = (
    Forbidden,
    HTTPException(status.HTTP_403_FORBIDDEN, "You don't have permission to perform this action"),
)
