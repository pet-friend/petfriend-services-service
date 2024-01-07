from fastapi import status, HTTPException

ADDRESS_NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
ADDRESS_EXISTS_ERROR = HTTPException(status.HTTP_409_CONFLICT, "The service already has an address")
