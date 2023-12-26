from sqlmodel import SQLModel

from .util import UUIDModel, TimestampModel


# Base model
class ExampleBase(SQLModel):
    public_attribute_1: str
    public_attribute_2: int


# What the user gets from the API (Base + id)
class ExampleRead(ExampleBase, UUIDModel):
    pass


# Actual data in database table (Base + id + timestamps)
class Example(ExampleRead, TimestampModel, table=True):
    __tablename__ = "basic"


# Required attributes for creating a new record
class ExampleCreate(ExampleBase):
    pass
