from datetime import datetime

from sqlmodel import Field, SQLModel
from pydantic import PositiveInt, BaseModel, AwareDatetime

from ..payments import PaymentStatus
from ..util import UUIDModel, Id, TZDateTime


class AppointmentBase(SQLModel):
    start: AwareDatetime = Field(sa_type=TZDateTime)


class AppointmentRead(AppointmentBase, UUIDModel):
    end: AwareDatetime = Field(sa_type=TZDateTime)
    status: PaymentStatus
    service_id: Id = Field(foreign_key="services.id")
    customer_id: Id


class Appointment(AppointmentRead, table=True):
    __tablename__ = "appointments"


class AppointmentCreate(BaseModel):
    start: datetime  # assumed to be in the service's timezone if naive


class AvailableAppointment(BaseModel):
    start: datetime
    end: datetime
    amount: PositiveInt
