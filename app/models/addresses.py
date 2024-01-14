from enum import StrEnum
from decimal import Decimal

from pydantic import field_validator, ValidationInfo, Field as PField
from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import SQLModel, Field

from .util import UUIDModel, TimestampModel, Id
from .constants.addresses import MISSING_APARTMENT_MSG


class AddressType(StrEnum):
    HOUSE = "house"
    APARTMENT = "apartment"
    OFFICE = "office"
    OTHER = "other"


# Base model
class AddressBase(SQLModel):
    country_code: CountryAlpha2
    region: str  # State, province, etc.
    city: str
    postal_code: str
    street: str
    street_number: str
    type: AddressType
    apartment: str | None = Field(default=None)
    latitude: Decimal = Field(max_digits=9, decimal_places=6)
    longitude: Decimal = Field(max_digits=9, decimal_places=6)

    model_config = {"validate_default": True}

    @field_validator("apartment")
    def validate_apartment(cls, apartment: str | None, info: ValidationInfo) -> str | None:
        if info.data["type"] != AddressType.APARTMENT:
            return None
        if not apartment:
            raise ValueError(MISSING_APARTMENT_MSG)
        return apartment


# What the user gets from the API (Base + id)
class AddressRead(AddressBase):
    pass


class AddressReadRenamed(AddressRead):
    id: Id = PField(serialization_alias="service_id")


# Actual data in database table (Base + id + timestamps)
class Address(AddressRead, UUIDModel, TimestampModel, table=True):
    __tablename__ = "addresses"


# Required attributes for creating a new record
class AddressCreate(AddressBase):
    pass
