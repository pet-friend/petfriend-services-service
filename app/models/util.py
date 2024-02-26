import uuid as uuid_pkg
from datetime import datetime
from typing import Any, BinaryIO, Protocol

from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Field, SQLModel


class HealthCheck(BaseModel):
    message: str


Id = uuid_pkg.UUID


class UUIDModel(SQLModel):
    id: Id = Field(default_factory=uuid_pkg.uuid4, primary_key=True)


class TimestampModel(SQLModel):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": text("current_timestamp")},
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("current_timestamp"),
            "onupdate": text("current_timestamp"),
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
