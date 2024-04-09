from fastapi import status, HTTPException


IMAGE_EXISTS_ERROR = (
    FileExistsError,
    HTTPException(status.HTTP_409_CONFLICT, "An image already already exists"),
)

INVALID_IMAGE_ERROR = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image")

IMAGE_NOT_FOUND_ERROR = (
    FileNotFoundError,
    HTTPException(status.HTTP_404_NOT_FOUND, "Image not found"),
)
