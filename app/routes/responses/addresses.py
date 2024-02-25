from fastapi import status, HTTPException

ADDRESS_NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
ADDRESS_EXISTS_ERROR = HTTPException(status.HTTP_409_CONFLICT, "The service already has an address")
NON_EXISTENT_ADDRESS_ERROR = HTTPException(
    status.HTTP_422_UNPROCESSABLE_ENTITY, "Could not find the location of the given address"
)
SERVICE_NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
