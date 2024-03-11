from fastapi import status, HTTPException

UNAUTHORIZED = HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid access token")
FORBIDDEN = HTTPException(
    status.HTTP_403_FORBIDDEN, "You don't have permission to perform this action"
)
