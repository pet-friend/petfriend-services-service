from typing import AsyncGenerator
from fastapi import Depends, status
from httpx import AsyncClient, Timeout

from app.exceptions.addresses import AddressNotFound
from app.exceptions.users import InvalidToken, UnknownUserError
from app.config import settings
from app.models.util import Id, Coordinates

REQUEST_TIMEOUT = Timeout(5, read=45)


async def users_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url=settings.USERS_SERVICE_URL, timeout=REQUEST_TIMEOUT) as client:
        yield client


class UsersService:
    def __init__(self, client: AsyncClient = Depends(users_client)) -> None:
        self.client = client

    async def validate_user(self, token: str) -> Id:
        response = await self.client.post("/validate", headers={"Authorization": f"Bearer {token}"})

        if response.is_success:
            result = response.json()
            return Id(result["user_id"])

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise InvalidToken(response.text)

        raise UnknownUserError(response.text)

    async def get_user_address_coordinates(self, user_id: Id, address_id: Id) -> Coordinates:
        response = await self.client.get(f"/users/{user_id}/addresses/{address_id}")

        if response.is_success:
            result = response.json()
            return Coordinates.model_validate(result)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise AddressNotFound

        raise UnknownUserError(response.text)
