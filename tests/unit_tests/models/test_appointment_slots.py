from datetime import timedelta, time

import pytest
from pydantic import BaseModel

from app.models.services import AppointmentSlotsBase, DayOfWeek, AppointmentSlotsList


class TestList(BaseModel):
    __test__ = False

    slots: AppointmentSlotsList


class TestAppointmentSlotsModel:
    async def test_appoinnment_slots_with_valid_fields(self) -> None:
        # Given
        create = {
            "day_of_week": 0,
            "start_time": "08:00",
            "appointment_duration": "00:05",
            "end_time": "09:00",
        }

        # When
        created = AppointmentSlotsBase.model_validate(create)

        # Then
        assert created.day_of_week == DayOfWeek.MONDAY
        assert created.start_time == time(hour=8)
        assert created.end_time == time(hour=9)
        assert created.appointment_duration == timedelta(minutes=5)

    async def test_appoinnment_slots_end_before_start(self) -> None:
        # Given
        create = {
            "day_of_week": 0,
            "start_time": "08:00",
            "appointment_duration": "00:30",
            "end_time": "07:30",
        }

        # When, Then
        with pytest.raises(ValueError):
            AppointmentSlotsBase.model_validate(create)

    async def test_appoinnment_slots_end_time_too_short(self) -> None:
        # Given
        create = {
            "day_of_week": 0,
            "start_time": "08:00",
            "appointment_duration": "00:30",
            "end_time": "08:10",
        }

        # When, Then
        with pytest.raises(ValueError):
            AppointmentSlotsBase.model_validate(create)

    async def test_appoinnment_slots_too_short(self) -> None:
        # Given
        create = {
            "day_of_week": 0,
            "start_time": "08:00",
            "appointment_duration": "00:01",
            "end_time": "09:00",
        }

        # When, Then
        with pytest.raises(ValueError):
            AppointmentSlotsBase.model_validate(create)

    async def test_appoinnment_slots_list_valid(self) -> None:
        # Given
        slots = [
            {
                "day_of_week": 0,
                "start_time": "08:00",
                "appointment_duration": "00:30",
                "end_time": "13:00",
            },
            {
                "day_of_week": 0,
                "start_time": "13:00",
                "appointment_duration": "00:15",
                "end_time": "14:00",
            },
            {
                "day_of_week": 1,
                "start_time": "08:00",
                "appointment_duration": "00:10",
                "end_time": "09:00",
            },
        ]

        # When
        created = TestList.model_validate({"slots": slots})

        # Then
        assert len(created.slots) == 3

    async def test_appoinnment_slots_list_overlap(self) -> None:
        # Given
        slots = [
            {
                "day_of_week": 0,
                "start_time": "08:00",
                "appointment_duration": "00:30",
                "end_time": "13:00",  # Ends at 13:00
            },
            {
                "day_of_week": 0,
                "start_time": "16:00",
                "appointment_duration": "00:15",
                "end_time": "17:00",
            },
            {
                "day_of_week": 0,
                "start_time": "12:00",  # Starts at 12:00
                "appointment_duration": "00:15",
                "end_time": "14:00",
            },
            {
                "day_of_week": 1,
                "start_time": "08:00",
                "appointment_duration": "00:10",
                "end_time": "09:00",
            },
        ]

        # When, Then
        with pytest.raises(ValueError):
            TestList.model_validate({"slots": slots})
