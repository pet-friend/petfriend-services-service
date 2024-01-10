from fastapi import status, HTTPException


IMAGE_EXISTS_ERROR = HTTPException(status.HTTP_409_CONFLICT, "The user already has an image")
INVALID_IMAGE_ERROR = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image")
IMAGE_NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")

# This error is not actually used in the code, it's just for route documentation.
# We can't use both IMAGE_NOT_FOUND_ERROR and USER_NOT_FOUND_ERROR for 404s in the docs.
NOT_FOUND_ERROR = HTTPException(status.HTTP_404_NOT_FOUND, "User or image not found")
