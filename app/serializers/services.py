from typing import Sequence

from pydantic import BaseModel

from app.models.services import ServiceRead, AppointmentRead


class ServiceList(BaseModel):
    services: Sequence[ServiceRead]
    amount: int


class AppointmentList(BaseModel):
    appointments: Sequence[AppointmentRead]
    amount: int
