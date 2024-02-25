from enum import StrEnum

from pydantic import field_validator, ValidationInfo, Field as PField
from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import SQLModel, Field

from .util import TimestampModel, Id
from .constants.addresses import MISSING_APARTMENT_MSG


class AddressType(StrEnum):
    HOUSE = "house"
    APARTMENT = "apartment"
    OFFICE = "office"
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


# What the user gets from the API (Base + id)
class AddressRead(AddressBase):
    id: Id = Field(foreign_key="services.id", primary_key=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AddressReadRenamed(AddressRead):
    id: Id = PField(serialization_alias="service_id")


# Actual data in database table (Base + id + timestamps)
class Address(AddressRead, TimestampModel, table=True):
    __tablename__ = "addresses"


# Required attributes for creating a new record
class AddressCreate(AddressBase):
    pass
