from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .routes.responses.auth import UNAUTHORIZED
from .exceptions.users import InvalidToken
from .models.util import Id
from .services.users import UsersService


oauth2_scheme = HTTPBearer(auto_error=False)


async def get_caller_id(request: Request) -> Id:
    user_id: Id | None = getattr(request.state, "user_id", None)
    if not user_id:
        # authenticate() was not called
        raise HTTPException(status_code=500, detail="User ID not found in request state")
    return user_id


async def get_caller_token(
    auth: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
) -> str:
    if auth is None:
        raise UNAUTHORIZED
    return auth.credentials


async def authenticate(
    req: Request,
    auth: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    users_service: UsersService = Depends(),
) -> Id:
    if auth is None:
        raise UNAUTHORIZED

    try:
        credentials = auth.credentials
        user_id = await users_service.validate_user(credentials)
    except (ValueError, InvalidToken) as exc:
        raise UNAUTHORIZED from exc

    setattr(req.state, "user_id", user_id)
    return user_id


async def validate_payments_key(
    api_key: str = Header(None, description="API Key", required=True),
) -> str:
    if api_key is not None and api_key == settings.PAYMENTS_API_KEY:
        return api_key

    raise UNAUTHORIZED
