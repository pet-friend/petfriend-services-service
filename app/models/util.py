# pylint: disable=E1102 # bugged with func.now()
from math import pi, radians, cos
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, BinaryIO, ClassVar, Protocol

from pydantic import AwareDatetime, BaseModel
from sqlalchemy import DateTime, TypeDecorator, func, Dialect
from sqlmodel import Field, SQLModel


class HealthCheck(BaseModel):
    message: str


Id = UUID


class UUIDModel(SQLModel):
    id: Id = Field(default_factory=uuid4, primary_key=True)


def now() -> datetime:
    return datetime.now(timezone.utc)


# pylint: disable=R0901 (too-many-ancestors)
class TZDateTime(TypeDecorator[datetime]):
    """
    Saes timezone-aware datetimes as timezone-naive UTC datetimes in any database. See:
    https://docs.sqlalchemy.org/en/20/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
    """

    python_type = datetime
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, _: Dialect) -> datetime | None:
        if value is None:
            return None
        # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
        if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
            raise TypeError("tzinfo is required")
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, _: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)

    def process_literal_param(self, value: datetime | None, _: Dialect) -> str:
        if value is None:
            return str(None)
        return f"'{value.astimezone(timezone.utc).isoformat()}'"


class TimestampModel(SQLModel):
    created_at: AwareDatetime = Field(
        default_factory=now,
        sa_type=TZDateTime,
        sa_column_kwargs={"server_default": func.now()},
    )

    updated_at: AwareDatetime = Field(
        default_factory=now,
        sa_type=TZDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
    )


class ImageUrlModel(SQLModel):
    image_url: str


class OptionalImageUrlModel(SQLModel):
    image_url: str | None = None


class File(Protocol):
    file: BinaryIO


class WithImage(Protocol):
    image_url: str | None

    def __init__(self, *, image_url: str | None, **kwargs: Any) -> None:
        pass


class Coordinates(SQLModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    EARTH_RADIUS_KM: ClassVar[float] = 6371.009
    KM_PER_DEG_LAT: ClassVar[float] = 2 * pi * EARTH_RADIUS_KM / 360.0

    def within(self, other: "Coordinates", max_distance_km: float) -> bool:
        return other.distance_to_squared(self) <= max_distance_km**2

    def distance_to_squared(self, other: "Coordinates") -> float:
        """
        Based on https://stackoverflow.com/a/5207131
        Should be decently accurate for small distances (a few km)
        """
        km_per_deg_long = self.KM_PER_DEG_LAT * cos(radians(self.latitude))

        return (self.KM_PER_DEG_LAT * (other.latitude - self.latitude)) ** 2 + (
            km_per_deg_long * (other.longitude - self.longitude)
        ) ** 2
