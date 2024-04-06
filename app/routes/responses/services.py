from fastapi import HTTPException, status

from app.exceptions.services import ServiceNotFound

SERVICE_NOT_FOUND_ERROR = (
    ServiceNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Service not found",
    ),
)
