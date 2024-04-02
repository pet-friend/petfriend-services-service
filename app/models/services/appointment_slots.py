from enum import Enum
from datetime import datetime, date, time, timedelta
from typing import Annotated

from sqlmodel import Field, SQLModel
from pydantic import AfterValidator, ValidationInfo, field_validator

from ..util import UUIDModel, Id


MIN_APPOINTMENT_DURATION = timedelta(minutes=5)


# Used 0 to 6 to match the standard library date.weekday() method
class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class AppointmentSlotsBase(SQLModel):
    day_of_week: DayOfWeek
    start_time: time
    appointment_duration: timedelta
    end_time: time

    @field_validator("appointment_duration", mode="after")
    @classmethod
    def validate_appointment_duration(cls, value: timedelta) -> timedelta:
        """
        Validates that the appointment duration is at least MIN_APPOINTMENT_DURATION
        """
        if value < MIN_APPOINTMENT_DURATION:
            raise ValueError(
                f"The appointment duration must be at least {MIN_APPOINTMENT_DURATION}"
            )

        return value

    @field_validator("end_time", mode="after")
    @classmethod
    def validate_end_time(cls, value: time, info: ValidationInfo) -> time:
        """
        Validates that the end time is after the start time and
        that at least one appointment fits in the time slot
        """
        if "appointment_duration" not in info.data:
            # validate_appointment_duration failed
            return value

        today = date.today()
        start_time: datetime = datetime.combine(today, info.data["start_time"])
        end_time: datetime = datetime.combine(today, value)
        duration: timedelta = info.data["appointment_duration"]
        if end_time < start_time + duration:
            raise ValueError("At least one appointment should fit in the time slot")

        return value


class AppointmentSlots(UUIDModel, AppointmentSlotsBase, table=True):
    __tablename__ = "appointment_slots"
    service_id: Id = Field(foreign_key="services.id")


def validate_appointment_slots_list(
    values: list[AppointmentSlotsBase],
) -> list[AppointmentSlotsBase]:
    """
    Checks that appointment slots in the same day dont overlap
    """
    slots_per_day: dict[DayOfWeek, list[AppointmentSlotsBase]] = {}
    for slot in values:
        slots_per_day.setdefault(slot.day_of_week, []).append(slot)

    # make sure slots dont overlap
    for day, slots in slots_per_day.items():
        slots.sort(key=lambda s: s.start_time)
        for i in range(1, len(slots)):
            if slots[i - 1].end_time > slots[i].start_time:
                raise ValueError(f"Appointment slots in {day} overlap")

    return values


AppointmentSlotsList = Annotated[
    list[AppointmentSlotsBase], AfterValidator(validate_appointment_slots_list)
]
