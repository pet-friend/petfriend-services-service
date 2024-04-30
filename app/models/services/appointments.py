from datetime import datetime
from decimal import Decimal
from typing import Generator

from sqlalchemy import PrimaryKeyConstraint
from sqlmodel import Field, Relationship
from pydantic import PositiveInt, BaseModel, AwareDatetime

from ..payments import PaymentStatusModel
from ..util import UUIDModel, Id, TZDateTime, TimestampModel
from .services import Service, ServiceRead
from .appointment_slots import AppointmentSlotsBase


class AppointmentBase(PaymentStatusModel, UUIDModel, TimestampModel):
    start: AwareDatetime = Field(sa_type=TZDateTime)
    end: AwareDatetime = Field(sa_type=TZDateTime)
    customer_id: Id
    customer_address_id: Id
    animal_id: Id
    price: Decimal = Field(max_digits=14, decimal_places=2, gt=0)


class AppointmentRead(AppointmentBase):
    service: ServiceRead


class Appointment(AppointmentBase, table=True):
    __tablename__ = "appointments"

    service_id: Id = Field(foreign_key="services.id", primary_key=True)
    service: Service = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    __table_args__ = (
        # Make sure the order of the PK is (service_id, id)
        PrimaryKeyConstraint("service_id", "id"),
    )


class AppointmentCreate(BaseModel):
    start: datetime  # assumed to be in the service's timezone if naive
    animal_id: Id


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
