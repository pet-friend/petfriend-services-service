from fastapi import status, HTTPException

ADDRESS_NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
NON_EXISTENT_ADDRESS_ERROR = HTTPException(
    status.HTTP_422_UNPROCESSABLE_ENTITY, "Could not find the location of the given address"
)
