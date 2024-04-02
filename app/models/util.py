from math import pi, radians, cos
import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import Any, BinaryIO, Protocol, cast, Type

from pydantic import BaseModel
from sqlalchemy import DateTime, func
from sqlmodel import Field, SQLModel


class HealthCheck(BaseModel):
    message: str


Id = uuid_pkg.UUID


class UUIDModel(SQLModel):
    id: Id = Field(default_factory=uuid_pkg.uuid4, primary_key=True)


def now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampModel(SQLModel):
    created_at: datetime = Field(
        default_factory=now,
        nullable=False,
        sa_type=cast(Type[Any], DateTime(timezone=True)),
        sa_column_kwargs={"server_default": func.now()},
    )

    updated_at: datetime = Field(
        default_factory=now,
        nullable=False,
        sa_type=cast(Type[Any], DateTime(timezone=True)),
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


EARTH_RADIUS_KM = 6371.009
KM_PER_DEG_LAT = 2 * pi * EARTH_RADIUS_KM / 360.0


def distance_squared(coords_base: Coordinates, other_coords: Coordinates) -> float:
    """
    Based on https://stackoverflow.com/a/5207131
    Should be decently accurate for small distances (a few km)
    """
    km_per_deg_long = KM_PER_DEG_LAT * cos(radians(coords_base.latitude))

    return (KM_PER_DEG_LAT * (other_coords.latitude - coords_base.latitude)) ** 2 + (
        km_per_deg_long * (other_coords.longitude - coords_base.longitude)
    ) ** 2
