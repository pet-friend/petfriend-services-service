from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.services import Service
from app.models.util import Id
from app.db import get_db
from app.repositories.util import service_distance_filter
from ..nearby_repository import NearbyRepository


class ServicesRepository(NearbyRepository[Service, Id | str, []]):
    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        super().__init__(Service, session, service_distance_filter)
