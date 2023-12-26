# How to create new models

### Steps

1. Create model. See [create_new_model](./create_new_models.md)
2. Create routes file inside `app/routes/` directory.
    - Example: `app/routes/users.py`
3. Create the repository file inside `app/repositories/`
    - Example: `app/repositories/users.py`
4. Create the repository
    - Example:
    ```
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db import get_db
    from app.models.users import User
    from app.repositories.base_repository import BaseRepository


    class UsersRepository(BaseRepository):
        def __init__(self, session: AsyncSession = Depends(get_db)):
            super().__init__(User, session=session)
    ```
    - Note that here were are inheriting from `BaseRepository`. We use this inheritance because it has already defined usefull basic methods.
  
5. Create the endpoint
    - Example: 
    ```
    from typing import List
from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.models.users import User
from app.repositories.users import UsersRepository

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", status_code=http_status.HTTP_201_CREATED)
async def create_user(
    data: User, user_repository: UsersRepository = Depends(UsersRepository)
) -> User:
    user = await user_repository.create(data)
    return user


@router.get("/{user_id}", status_code=http_status.HTTP_200_OK)
async def get_user_by_uuid(
    user_id: str, user_repository: UsersRepository = Depends(UsersRepository)
) -> User:
    user = await user_repository.get(user_id)
    return user


@router.get("/", status_code=http_status.HTTP_200_OK)
async def get_users(
    user_repository: UsersRepository = Depends(UsersRepository)
) -> List[User]:
    user = await user_repository.get_all()
    return user


@router.patch("/{user_id}", status_code=http_status.HTTP_200_OK)
async def patch_user_by_uuid(
    user_id: str,
    data: User,
    user_repository: UsersRepository = Depends(UsersRepository),
) -> User:
    user = await user_repository.update(_id=user_id, data=data)
    return user


@router.delete("/{user_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_user_by_uuid(
    user_id: str, user_repository: UsersRepository = Depends(UsersRepository)
) -> None:
    await user_repository.delete(_id=user_id)

    ```

6. Add users endpoint to `/app/router.py`
    - Example: 
    ```
    from fastapi import APIRouter
    from app.routes import users

    api_router = APIRouter()

    api_router.include_router(users_router)
    ```