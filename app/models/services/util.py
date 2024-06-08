from enum import StrEnum
from datetime import time
import zoneinfo
from typing import Annotated

from pydantic import AfterValidator

Timezone = StrEnum("Timezone", {x: x for x in zoneinfo.available_timezones()})  # type: ignore

DEFAULT_TIMEZONE = "America/Argentina/Buenos_Aires"
assert DEFAULT_TIMEZONE in Timezone


def check_naive_time(value: time) -> time:
    if value.tzinfo is not None:
        raise ValueError("Time must be time zone naive")
    return value


NaiveTime = Annotated[time, AfterValidator(check_naive_time)]
