from typing import Sequence
from enum import StrEnum
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import String

from .appointment_slots import AppointmentSlotsBase, AppointmentSlots, AppointmentSlotsList
from ..addresses import Address, AddressRead, AddressCreate, ServiceAddressLink
from ..util import Id, TimestampModel, OptionalImageUrlModel, UUIDModel
from .util import Timezone, DEFAULT_TIMEZONE


class ServiceCategory(StrEnum):
    GROOMING = "grooming"  # estética e higiene
    TRAINING = "training"  # entrenamiento/adiestramiento
    WALKING = "walking"  # paseo
    HEALTH = "health"  # veterinaria/salud
    CARE = "care"  # guarderias y cuidadores
    OTHER = "other"  # otro


class ServiceBase(SQLModel):
    name: str
    description: str | None = None
    appointment_days_in_advance: int = Field(ge=0)
    # How close the service provider needs to be to the uer
    # in order to be available for the user
    customer_range_km: float
    # If True, the service is provided at the service's address
    is_home_service: bool = False
    category: ServiceCategory
    timezone: Timezone = Field(default=DEFAULT_TIMEZONE, sa_type=String)


# Public database fields
class ServicePublic(UUIDModel, ServiceBase):
    owner_id: Id


# What the user gets from the API (Public + image + address + slots)
class ServiceRead(ServicePublic, OptionalImageUrlModel):
    appointment_slots: Sequence[AppointmentSlotsBase]
    address: AddressRead


# Actual data in database table (Base + id + timestamps)
class Service(ServicePublic, TimestampModel, table=True):
    __tablename__ = "services"

    appointment_slots: list[AppointmentSlots] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )

    # pylint:disable=duplicate-code
    address: Address = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "single_parent": True,
        },
        link_model=ServiceAddressLink,
    )

    def to_tz(self, dt: datetime) -> datetime:
        """
        Returns the given timestamp adjusted to the service's timezone.
        If the given timestamp is naive, it is assumed to be in the service's timezone.
        """
        tz = ZoneInfo(self.timezone)
        if not dt.tzinfo or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=tz)
        return dt.astimezone(tz)

    @property
    def range_km(self) -> float:
        return self.customer_range_km


# Required attributes for creating a new record
class ServiceCreate(ServiceBase):
    address: AddressCreate
    appointment_slots: AppointmentSlotsList
