from datetime import datetime
from typing import Generator

from sqlalchemy import PrimaryKeyConstraint
from sqlmodel import Field, Relationship
from pydantic import PositiveInt, BaseModel, AwareDatetime

from ..services import Service
from ..payments import PaymentStatusModel
from ..util import UUIDModel, Id, TZDateTime, TimestampModel
from .appointment_slots import AppointmentSlotsBase


class AppointmentBase(PaymentStatusModel, UUIDModel, TimestampModel):
    start: AwareDatetime = Field(sa_type=TZDateTime)
    end: AwareDatetime = Field(sa_type=TZDateTime)
    service_id: Id = Field(foreign_key="services.id", primary_key=True)
    customer_id: Id
    customer_address_id: Id


class AppointmentRead(AppointmentBase):
    pass


class Appointment(AppointmentRead, table=True):
    __tablename__ = "appointments"

    service: Service = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    __table_args__ = (
        # Make sure the order of the PK is (service_id, id)
        PrimaryKeyConstraint("service_id", "id"),
    )


class AppointmentCreate(BaseModel):
    start: datetime  # assumed to be in the service's timezone if naive


class AvailableAppointment(BaseModel):
    start: datetime
    end: datetime
    amount: PositiveInt


class AvailableAppointmentsForSlots(BaseModel):
    slots_configuration: AppointmentSlotsBase
    available_appointments: list[AvailableAppointment]


class AvailableAppointmentsList(list[AvailableAppointmentsForSlots]):
    def iterate_appointments(
        self,
    ) -> Generator[tuple[AppointmentSlotsBase, AvailableAppointment], None, None]:
        for available_for_slots in self:
            for available_appointment in available_for_slots.available_appointments:
                yield available_for_slots.slots_configuration, available_appointment
