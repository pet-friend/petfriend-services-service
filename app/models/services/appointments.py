from datetime import datetime

from sqlmodel import Field, SQLModel
from pydantic import PositiveInt, BaseModel

from ..payments import PaymentStatus
from ..util import UUIDModel, Id


class AppointmentBase(SQLModel):
    start: datetime


class AppointmentRead(AppointmentBase, UUIDModel):
    end: datetime
    status: PaymentStatus
    service_id: Id = Field(foreign_key="services.id")
    customer_id: Id


class Appointment(AppointmentRead, table=True):
    __tablename__ = "appointments"


class AppointmentCreate(AppointmentBase):
    pass


class AvailableAppointment(BaseModel):
    start: datetime
    end: datetime
    amount: PositiveInt
