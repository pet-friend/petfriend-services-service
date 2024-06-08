from typing import Sequence, Any
from datetime import datetime

from fastapi import Depends
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import desc

from app.models.services import Appointment
from app.models.util import Id
from app.db import get_db
from ..base_repository import BaseRepository


class AppointmentsRepository(BaseRepository[Appointment, tuple[Id | str, Id | str]]):
    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        super().__init__(Appointment, session)

    async def get_all_by_range(
        self,
        range_start: datetime | None,
        range_end: datetime | None,
        return_partial: bool = False,
        limit: int | None = None,
        skip: int = 0,
        **filters: Any
    ) -> Sequence[Appointment]:
        """
        Return all of the appointments that take place in the given range.
        If return_partial is False, only return appointments that are fully
        contained in the range will be returned.
        If return_partial is True, appointments that partially overlap with the
        range will also be returned.
        `range_start` and `range_end` must be timezone-aware datetimes.
        """
        # TZDateTime handles converting the aware datetimes to UTC
        query = select(Appointment)
        where = self._common_filters(**filters)
        if range_start:
            if return_partial:
                where = and_(Appointment.end > range_start, where)
            else:
                where = and_(Appointment.start >= range_start, where)
        if range_end:
            if return_partial:
                where = and_(Appointment.start < range_end, where)
            else:
                where = and_(Appointment.end <= range_end, where)
        query = (
            query.where(where)
            .offset(skip)
            .limit(limit)
            .order_by(desc(Appointment.start))  # type: ignore
        )
        result = await self.db.exec(query)
        return result.all()
