from fastapi import status, HTTPException

from app.exceptions.animals import InvalidAnimal


FORBIDDEN = (
    InvalidAnimal,
    HTTPException(
        status.HTTP_400_BAD_REQUEST, "The user does not have an animal with the provided ID"
    ),
)
