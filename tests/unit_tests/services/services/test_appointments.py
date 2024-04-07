from uuid import uuid4
from unittest.mock import AsyncMock
from datetime import datetime, time, timedelta, date
from zoneinfo import ZoneInfo

from app.models.payments import PaymentStatus
from app.models.services import Service, AppointmentSlots, DayOfWeek, AvailableAppointment
from app.models.addresses import Address
from app.models.services.appointments import Appointment, AppointmentCreate
from app.repositories.services import AppointmentsRepository
from app.services.services import AppointmentsService, ServicesService
from tests.factories.service_factories import ServiceCreateFactory
from tests.util import CustomMatcher


class TestServicesService:
    def setup_method(self) -> None:
        self.service_create = ServiceCreateFactory().build()

        self.owner_id = uuid4()
        service_id = uuid4()
        self.service_model = Service(
            id=service_id,
            owner_id=self.owner_id,
            appointment_slots=[
                AppointmentSlots(service_id=service_id, **slot_create.model_dump())
                for slot_create in self.service_create.appointment_slots
            ],
            address=Address(latitude=0, longitude=0, **self.service_create.address.model_dump()),
            **self.service_create.model_dump(exclude={"address", "appointment_slots"})
        )

        self.repository = AsyncMock(spec=AppointmentsRepository)
        self.services_service = AsyncMock(spec=ServicesService)
        self.service = AppointmentsService(self.repository, self.services_service)

    async def test_get_available_appointments_simple(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_first_one_finished(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(8, 40), tz)  # It's 8:40AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            # 8:00 - 8:30 should not be available as it is 8:40
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_one_overlap(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
            ),
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=2,  # Only 2 available
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_one_overlap_is_removed(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=1,  # Only 1 appointment per slot
            )
        ]
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
            ),
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=1,
            ),
        ]

    async def test_get_available_appointments_one_overlap_two_times(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = [
            # this appointment overlaps with both slots,
            # which can happen if the service provider changes the
            # slots configuration after the appointment was made
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 45), tz),
                status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
            ),
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=2,  # Only 2 available
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=2,  # Only 2 available
            ),
        ]

    async def test_get_available_appointments_should_get_next_week(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        # I can make appointments for the next week:
        self.service_model.appointment_days_in_advance = 7
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(8, 30),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now, 7)
        next_week = now.date() + timedelta(weeks=1)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(next_week, time(8, 0), tz),
                end=datetime.combine(next_week, time(8, 30), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_should_get_next_week_with_overlap(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        # I can make appointments for the next week:
        self.service_model.appointment_days_in_advance = 7
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(8, 30),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 45), tz),
                status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
            ),
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now, 7)
        next_week = now.date() + timedelta(weeks=1)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=2,
            ),
            AvailableAppointment(
                start=datetime.combine(next_week, time(8, 0), tz),
                end=datetime.combine(next_week, time(8, 30), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_many_slots(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        tomorrow = DayOfWeek.from_weekday((now.date() + timedelta(days=1)).weekday())
        self.service_model.appointment_days_in_advance = 1
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            ),
            AppointmentSlots(
                start_day=today,
                start_time=time(13, 0),
                end_time=time(14, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=45),
                max_appointments_per_slot=1,
            ),
            AppointmentSlots(
                start_day=tomorrow,
                start_time=time(10, 0),
                end_time=time(18, 0),
                end_day=today,
                appointment_duration=timedelta(hours=4),
                max_appointments_per_slot=2,
            ),
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now, 1)
        tomorrow_date = now.date() + timedelta(days=1)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(13, 0), tz),
                end=datetime.combine(now.date(), time(13, 45), tz),
                amount=1,
            ),
            AvailableAppointment(
                start=datetime.combine(tomorrow_date, time(10, 0), tz),
                end=datetime.combine(tomorrow_date, time(14, 0), tz),
                amount=2,
            ),
            AvailableAppointment(
                start=datetime.combine(tomorrow_date, time(14, 0), tz),
                end=datetime.combine(tomorrow_date, time(18, 0), tz),
                amount=2,
            ),
        ]

    async def test_get_available_appointments_many_slots_with_overlap(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        tomorrow = DayOfWeek.from_weekday((now.date() + timedelta(days=1)).weekday())
        self.service_model.appointment_days_in_advance = 1
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            ),
            AppointmentSlots(
                start_day=today,
                start_time=time(13, 0),
                end_time=time(14, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=45),
                max_appointments_per_slot=1,
            ),
            AppointmentSlots(
                start_day=tomorrow,
                start_time=time(10, 0),
                end_time=time(18, 0),
                end_day=today,
                appointment_duration=timedelta(hours=4),
                max_appointments_per_slot=2,
            ),
        ]
        tomorrow_date = now.date() + timedelta(days=1)
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(13, 30), tz),
                end=datetime.combine(tomorrow_date, time(14, 00), tz),
                status=PaymentStatus.IN_PROGRESS,
                customer_id=uuid4(),
            )
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now, 1)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 0), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(tomorrow_date, time(10, 0), tz),
                end=datetime.combine(tomorrow_date, time(14, 0), tz),
                amount=1,
            ),
            AvailableAppointment(
                start=datetime.combine(tomorrow_date, time(14, 0), tz),
                end=datetime.combine(tomorrow_date, time(18, 0), tz),
                amount=2,
            ),
        ]

    async def test_get_available_appointments_with_after(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        after = datetime.combine(now.date(), time(8, 30), tz)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, after=after
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=after)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_with_before(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        before = datetime.combine(now.date(), time(8, 30), tz)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, before=before
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, before=before)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 00), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_with_before_partial(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        before = datetime.combine(now.date(), time(8, 45), tz)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, before=before
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, before=before)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 00), tz),
                end=datetime.combine(now.date(), time(8, 30), tz),
                amount=3,
            ),
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=3,
            ),
        ]

    async def test_get_available_appointments_with_after_and_overlap(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(7, 0), tz),
                end=datetime.combine(now.date(), time(8, 45), tz),
                status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
            )
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        after = datetime.combine(now.date(), time(8, 40), tz)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, after=after
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=after)
        assert available_appointments == [
            AvailableAppointment(
                start=datetime.combine(now.date(), time(8, 30), tz),
                end=datetime.combine(now.date(), time(9, 0), tz),
                amount=2,
            ),
        ]

    async def test_create_appointment(self) -> None:
        # Given
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), time(1, 0), tz)  # It's 1:00AM
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = 0
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=3,
            )
        ]
        # self.repository.create.return_value = appointment
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model
        self.repository.save.side_effect = lambda x: x

        # When
        start = datetime.combine(now.date(), time(8, 0), tz)
        customer_id = uuid4()
        created_appointment = await self.service.create_appointment(
            AppointmentCreate(start=start),
            self.service_model.id,
            customer_id=customer_id,
            now=now,
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=start)
        self.repository.save.assert_called_once_with(created_appointment)
        assert created_appointment.start == datetime.combine(now.date(), time(8, 0), tz)
        assert created_appointment.end == datetime.combine(now.date(), time(8, 30), tz)
        assert created_appointment.status == PaymentStatus.CREATED
        assert created_appointment.service_id == self.service_model.id
        assert created_appointment.customer_id == customer_id

    def assert_repo_get_all_by_range(
        self,
        now: datetime,
        days_in_advance: int = 0,
        *,
        after: datetime | None = None,
        before: datetime | None = None
    ) -> None:
        next_day_00 = datetime.combine(now.date(), time(0, 0), now.tzinfo) + timedelta(
            days=days_in_advance + 1
        )
        before = min(before, next_day_00) if before else next_day_00
        after_matcher = (
            max(after, now)
            if after
            else CustomMatcher[datetime](lambda t: t - now < timedelta(seconds=2))  # ~now
        )
        self.repository.get_all_by_range.assert_called_once_with(
            after_matcher,
            before,
            service_id=self.service_model.id,
            status=CustomMatcher[list[PaymentStatus]](
                lambda s: len(set(s)) == 3 and PaymentStatus.CANCELLED not in s
            ),
        )
