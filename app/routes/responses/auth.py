from fastapi import status, HTTPException

UNAUTHORIZED = HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid access token")
