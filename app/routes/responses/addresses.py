from fastapi import status, HTTPException

from app.exceptions.addresses import AddressNotFound, NonExistentAddress

ADDRESS_NOT_FOUND_ERROR = (
    AddressNotFound,
    HTTPException(status.HTTP_404_NOT_FOUND, "Address not found"),
)

NON_EXISTENT_ADDRESS_ERROR = (
    NonExistentAddress,
    HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY, "Could not find the location of the given address"
    ),
)
