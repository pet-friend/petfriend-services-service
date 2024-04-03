from typing import Sequence

from pydantic import BaseModel

from app.models.services import ServiceRead


class ServiceList(BaseModel):
    services: Sequence[ServiceRead]
    amount: int
