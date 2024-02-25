from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Relationship

from .addresses import Address
from .util import UUIDModel, TimestampModel

if TYPE_CHECKING:
    from .stores import Store


class ServiceType(StrEnum):
    STORE = "store"


# Actual data in database table (Base + id + timestamps)
class Service(UUIDModel, TimestampModel, table=True):
    __tablename__ = "services"

    address: Address | None = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )

    type: ServiceType
    store: Optional["Store"] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
        back_populates="service",
    )
