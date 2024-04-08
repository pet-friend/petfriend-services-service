from datetime import datetime

from sqlmodel import Field
from pydantic import PositiveInt, BaseModel, AwareDatetime


from ..payments import PaymentStatusModel
from ..util import UUIDModel, Id, TZDateTime, TimestampModel
from .appointment_slots import AppointmentSlotsBase


class AppointmentBase(PaymentStatusModel, UUIDModel, TimestampModel):
    start: AwareDatetime = Field(sa_type=TZDateTime)
    end: AwareDatetime = Field(sa_type=TZDateTime)
    service_id: Id = Field(foreign_key="services.id")
    customer_id: Id


class AppointmentRead(AppointmentBase):
    pass


class Appointment(AppointmentRead, table=True):
    __tablename__ = "appointments"


class AppointmentCreate(BaseModel):
    start: datetime  # assumed to be in the service's timezone if naive


class AvailableAppointment(BaseModel):
    start: datetime
    end: datetime
    amount: PositiveInt
    from_slots: AppointmentSlotsBase
