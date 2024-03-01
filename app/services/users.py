from httpx import AsyncClient

from app.exceptions.users import InvalidToken, UnknownUserError
from app.config import settings
from app.models.util import Id


class UsersService:
    users_service_url: str = settings.USERS_SERVICE_URL

    async def validate_user(self, token: str) -> Id:
        client = AsyncClient(base_url=self.users_service_url)
        response = await client.post("/validate", headers={"Authorization": f"Bearer {token}"})

        if response.is_success:
            result = response.json()
            return Id(result["user_id"])

        if response.status_code == 401:
            raise InvalidToken(response.text)

        raise UnknownUserError(response.text)
