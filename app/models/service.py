from enum import StrEnum
from sqlmodel import Relationship

from .addresses import Address
from .util import UUIDModel, TimestampModel


class ServiceType(StrEnum):
    STORE = "store"


# Actual data in database table (Base + id + timestamps)
class Service(UUIDModel, TimestampModel, table=True):
    __tablename__ = "services"

    type: ServiceType
    address: Address | None = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
