from datetime import timedelta, time

import pytest
from pydantic import BaseModel

from app.exceptions.appointments import AppointmentSlotsCantOverlap
from app.models.services import AppointmentSlotsBase, DayOfWeek, AppointmentSlotsList


class TestList(BaseModel):
    __test__ = False

    slots: AppointmentSlotsList


class TestAppointmentSlotsModel:
    async def test_appointment_slots_with_valid_fields(self) -> None:
        # Given
        create = {
            "start_day": "monday",
            "start_time": "08:00",
            "appointment_duration": "00:05",
            "appointment_price": "50",
            "end_time": "09:00",
            "end_day": "monday",
        }

        # When
        created = AppointmentSlotsBase.model_validate(create)

        # Then
        assert created.start_day == DayOfWeek.MONDAY
        assert created.start_time == time(hour=8)
        assert created.end_time == time(hour=9)
        assert created.end_day == DayOfWeek.MONDAY
        assert created.appointment_duration == timedelta(minutes=5)

    async def test_appointment_slots_end_before_start(self) -> None:
        # Given
        create = {
            "start_day": "monday",
            "start_time": "08:00",
            "appointment_duration": "00:30",
            "appointment_price": "50",
            "end_time": "07:30",
            "end_day": "monday",
        }

        # When, Then
        with pytest.raises(ValueError):
            AppointmentSlotsBase.model_validate(create)

    async def test_appointment_slots_end_time_too_short(self) -> None:
        # Given
        create = {
            "start_day": "monday",
            "start_time": "08:00",
            "appointment_duration": "00:30",
            "appointment_price": "50",
            "end_time": "08:10",
            "end_day": "monday",
        }

        # When, Then
        with pytest.raises(ValueError):
            AppointmentSlotsBase.model_validate(create)

    async def test_appointment_slots_too_short(self) -> None:
        # Given
        create = {
            "start_day": "monday",
            "start_time": "08:00",
            "appointment_duration": "00:01",
            "appointment_price": "50",
            "end_time": "09:00",
            "end_day": "monday",
        }

        # When, Then
        with pytest.raises(ValueError):
            AppointmentSlotsBase.model_validate(create)

    async def test_appointment_slots_list_valid(self) -> None:
        # Given
        slots = [
            {
                "start_day": "monday",
                "start_time": "08:00",
                "appointment_duration": "00:30",
                "appointment_price": "50",
                "end_time": "13:00",
                "end_day": "monday",
            },
            {
                "start_day": "monday",
                "start_time": "13:00",
                "appointment_duration": "00:15",
                "appointment_price": "50",
                "end_time": "14:00",
                "end_day": "monday",
            },
            {
                "start_day": "tuesday",
                "start_time": "08:00",
                "appointment_duration": "00:10",
                "appointment_price": "50",
                "end_time": "09:00",
                "end_day": "tuesday",
            },
        ]

        # When
        created = TestList.model_validate({"slots": slots})

        # Then
        assert len(created.slots) == 3

    async def test_appointment_slots_list_overlap(self) -> None:
        # Given
        slots = [
            {
                "start_day": "monday",
                "start_time": "08:00",
                "appointment_duration": "00:30",
                "appointment_price": "50",
                "end_time": "13:00",  # Ends at 13:00
                "end_day": "monday",
            },
            {
                "start_day": "monday",
                "start_time": "16:00",
                "appointment_duration": "00:15",
                "appointment_price": "50",
                "end_time": "17:00",
                "end_day": "monday",
            },
            {
                "start_day": "monday",
                "start_time": "12:00",  # Starts at 12:00
                "appointment_duration": "00:15",
                "appointment_price": "50",
                "end_time": "14:00",
                "end_day": "monday",
            },
            {
                "start_day": "tuesday",
                "start_time": "08:00",
                "appointment_duration": "00:10",
                "appointment_price": "50",
                "end_time": "09:00",
                "end_day": "monday",
            },
        ]

        # When, Then
        with pytest.raises(AppointmentSlotsCantOverlap):
            TestList.model_validate({"slots": slots})

    async def test_appointment_slots_different_days_is_valid(self) -> None:
        # Given
        create = {
            "start_day": "wednesday",
            "start_time": "22:00",
            "appointment_duration": "11:00",
            "appointment_price": "50",
            "end_time": "09:00",
            "end_day": "thursday",
        }

        # When
        created = AppointmentSlotsBase.model_validate(create)

        # Then
        assert created.start_day == DayOfWeek.WEDNESDAY
        assert created.start_time == time(hour=22)
        assert created.end_time == time(hour=9)
        assert created.end_day == DayOfWeek.THURSDAY
        assert created.appointment_duration == timedelta(hours=11)

    async def test_appointment_slots_list_different_weeks_is_valid(self) -> None:
        # Given
        slots = [
            {
                "start_day": "tuesday",
                "start_time": "08:00",
                "appointment_duration": "10:00",
                "appointment_price": "50",
                "end_time": "13:00",
                "end_day": "friday",
            },
            {
                "start_day": "saturday",
                "start_time": "08:00",
                "appointment_duration": "10:00",
                "appointment_price": "50",
                "end_time": "13:00",
                "end_day": "monday",
            },
        ]

        # When
        created = TestList.model_validate({"slots": slots})

        # Then
        assert len(created.slots) == 2

    async def test_appointment_slots_list_different_weeks_invalid(self) -> None:
        # Given
        slots = [
            {
                "start_day": "sunday",
                "start_time": "22:00",
                "appointment_duration": "01:00",
                "appointment_price": "50",
                "end_time": "08:00",
                "end_day": "monday",
            },
            {
                "start_day": "monday",
                "start_time": "07:00",
                "appointment_duration": "00:30",
                "appointment_price": "50",
                "end_time": "13:00",
                "end_day": "monday",
            },
        ]

        # When, Then
        with pytest.raises(AppointmentSlotsCantOverlap):
            TestList.model_validate({"slots": slots})
