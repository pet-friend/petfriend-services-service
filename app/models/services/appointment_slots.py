from enum import StrEnum
from typing import Self, Annotated
from datetime import datetime, timedelta, timezone

from sqlmodel import Field, SQLModel
from pydantic import AfterValidator, field_validator, model_validator

from ..util import UUIDModel, Id
from .util import NaiveTime


MIN_APPOINTMENT_DURATION = timedelta(minutes=5)


class DayOfWeek(StrEnum):
    # Starts on Monday to match the date.weekday() method
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

    @classmethod
    def from_weekday(cls, weekday: int) -> Self:
        return list(cls)[weekday]

    def to_weekday(self) -> int:
        return list(DayOfWeek).index(self)


class AppointmentSlotsBase(SQLModel):
    start_day: DayOfWeek
    start_time: NaiveTime
    appointment_duration: timedelta
    end_day: DayOfWeek
    end_time: NaiveTime
    max_appointments_per_slot: int = Field(1, gt=0)

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

    @model_validator(mode="after")
    def validate_slot_fits(self) -> Self:
        """
        Validates that the end time is after the start time and
        that at least one appointment fits in the time slot
        """
        start_time, end_time = self.get_current_timestamps()
        if end_time < start_time + self.appointment_duration:
            raise ValueError("At least one appointment should fit in the time slot")
        return self

    def get_current_timestamps(
        self, now: datetime | None = None, tz: timezone = timezone.utc
    ) -> tuple[datetime, datetime]:
        """
        Returns the start timestamp and end timestamp for the current or next
        occurrence of the slot.
        There are three possible cases:
        - The slot already finished this week: next week timestamps are returned
        - The slot is currently happening: current timestamps are returned
        - The slot is in the future: next occurrence timestamps are returned
        """
        now = now or datetime.now(tz)
        today = now.date()

        day_0 = today - timedelta(days=today.weekday())
        start_date = day_0 + timedelta(days=self.start_day.to_weekday())
        end_date = day_0 + timedelta(days=self.end_day.to_weekday())
        if end_date < start_date:
            # e.g. start_day = friday, end_day = tuesday
            # push friday to the previous week
            start_date -= timedelta(weeks=1)

        start_time = datetime.combine(start_date, self.start_time, tz)
        end_time = datetime.combine(end_date, self.end_time, tz)

        if end_time < now:
            # e.g. end_time was on tuesday but it's already wednesday
            start_time += timedelta(weeks=1)
            end_time += timedelta(weeks=1)

        return start_time, end_time


class AppointmentSlots(UUIDModel, AppointmentSlotsBase, table=True):
    __tablename__ = "appointment_slots"
    service_id: Id = Field(foreign_key="services.id")


def validate_appointment_slots_list(
    values: list[AppointmentSlotsBase],
) -> list[AppointmentSlotsBase]:
    """
    Checks that appointment slots don't overlap
    """
    if len(values) <= 1:
        return values

    now = datetime.now(timezone.utc)
    slots = [(s, *s.get_current_timestamps(now)) for s in values]
    sorted_slots = sorted(slots, key=lambda s: s[1])

    # make sure to check the last slot with the first slot
    end_prev = sorted_slots[-1][2] - timedelta(weeks=1)
    for i, (slot, start_current, end_current) in enumerate(sorted_slots):
        if end_prev > start_current:
            prev_slot = sorted_slots[i - 1][0]
            raise ValueError(
                "Appointment slots cannot overlap (slot ends on"
                f" {prev_slot.end_day.capitalize()} at {prev_slot.end_time} and another slot"
                f" starts on {slot.start_day.capitalize()} at {slot.start_time})"
            )
        end_prev = end_current

    return values


AppointmentSlotsList = Annotated[
    list[AppointmentSlotsBase], AfterValidator(validate_appointment_slots_list)
]
