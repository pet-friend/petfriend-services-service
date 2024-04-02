from datetime import date, time

from sqlmodel import Field, SQLModel

from ..util import UUIDModel, Id


class AppointmentBase(SQLModel):
    date: date
    start_time: time


class AppointmentRead(AppointmentBase, UUIDModel):
    service_id: Id = Field(foreign_key="services.id")
    customer_id: Id
    end_time: time


class Appointment(AppointmentRead, table=True):
    __tablename__ = "appointments"


class AppointmentCreate(AppointmentBase):
    pass
