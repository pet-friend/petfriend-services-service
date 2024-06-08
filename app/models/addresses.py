from enum import StrEnum

from pydantic import field_validator, ValidationInfo
from pydantic_extra_types.country import CountryAlpha2
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field

from .util import Coordinates, Id, TimestampModel, UUIDModel
from .constants.addresses import MISSING_APARTMENT_MSG


class AddressType(StrEnum):
    HOUSE = "house"
    APARTMENT = "apartment"
    OFFICE = "office"
    STOREFRONT = "storefront"
    OTHER = "other"


# Base model
class AddressBase(SQLModel):
    street: str
    street_number: str
    city: str
    region: str  # State, province, etc.
    country_code: CountryAlpha2
    type: AddressType
    apartment: str | None = Field(default=None)

    model_config = {"validate_default": True}

    @field_validator("apartment")
    def validate_apartment(cls, apartment: str | None, info: ValidationInfo) -> str | None:
        if info.data["type"] != AddressType.APARTMENT:
            return None
        if not apartment:
            raise ValueError(MISSING_APARTMENT_MSG)
        return apartment


# What the user gets from the API (Base + coordinates)
class AddressRead(AddressBase, Coordinates):
    pass


# Actual data in database table (Base + id + timestamps)
class Address(AddressRead, UUIDModel, TimestampModel, table=True):
    __tablename__ = "addresses"


# Required attributes for creating a new record
class AddressCreate(AddressBase):
    pass


# Use a link table to allow for both stores and services to have a relationship with
# the address table, and to cascade delete the address when the store/service is deleted


class StoreAddressLink(SQLModel, table=True):
    __tablename__ = "store_address_link"

    store_id: Id = Field(primary_key=True, foreign_key="stores.id")
    address_id: Id = Field(foreign_key="addresses.id")

    __table_args__ = (UniqueConstraint("address_id", name="store_address_link_address_id_uq"),)


class ServiceAddressLink(SQLModel, table=True):
    __tablename__ = "service_address_link"

    service_id: Id = Field(primary_key=True, foreign_key="services.id")
    address_id: Id = Field(foreign_key="addresses.id")

    __table_args__ = (UniqueConstraint("address_id", name="service_address_link_address_id_uq"),)
