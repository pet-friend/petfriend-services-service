from typing import AsyncGenerator
from fastapi import Depends
from httpx import AsyncClient, Timeout

from app.exceptions.animals import InvalidAnimal
from app.config import settings
from app.models.util import Id

REQUEST_TIMEOUT = Timeout(5, read=45)


async def animals_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        base_url=settings.ANIMALS_SERVICE_URL, timeout=REQUEST_TIMEOUT
    ) as client:
        yield client


class AnimalsService:
    def __init__(self, client: AsyncClient = Depends(animals_client)) -> None:
        self.client = client

    async def validate_animal(self, user_id: Id, animal_id: Id, token: str) -> None:
        response = await self.client.get(
            f"/animals/{animal_id}", headers={"Authorization": f"Bearer {token}"}
        )

        if response.is_success and response.json().get("owner", None) == str(user_id):
            return

        raise InvalidAnimal()
