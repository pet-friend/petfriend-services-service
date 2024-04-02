from sqlmodel import Field, Relationship, SQLModel


from .appointment_slots import AppointmentSlotsBase, AppointmentSlots, AppointmentSlotsList
from ..addresses import Address, AddressRead, AddressCreate, ServiceAddressLink
from ..util import Id, TimestampModel, OptionalImageUrlModel, UUIDModel


class ServiceBase(SQLModel):
    name: str
    description: str | None = None
    appointment_days_in_advance: int = Field(ge=0)
    # If None, the service is provided at the service's address
    home_service_range_km: float | None = None


# Public database fields
class ServicePublic(UUIDModel, ServiceBase):
    owner_id: Id


# What the user gets from the API (Public + image + slots)
class ServiceRead(ServicePublic, OptionalImageUrlModel):
    appointment_slots: list[AppointmentSlotsBase]
    address: AddressRead


# Actual data in database table (Base + id + timestamps)
class Service(ServicePublic, TimestampModel, table=True):
    __tablename__ = "services"

    appointment_slots: list[AppointmentSlots] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )

    address: Address = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "single_parent": True,
        },
        link_model=ServiceAddressLink,
    )


# Required attributes for creating a new record
class ServiceCreate(ServiceBase):
    address: AddressCreate
    appointment_slots: AppointmentSlotsList
