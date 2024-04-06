from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class PaymentStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


PaymentStatusUpdate = Literal[
    PaymentStatus.IN_PROGRESS, PaymentStatus.COMPLETED, PaymentStatus.CANCELLED
]


class PaymentUpdate(BaseModel):
    status: PaymentStatusUpdate
