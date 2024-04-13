from decimal import Decimal
from typing import Any
from uuid import uuid4
from unittest.mock import AsyncMock
from datetime import datetime, time, timedelta, date
from zoneinfo import ZoneInfo

import pytest

from app.config import settings
from app.exceptions.appointments import AppointmentNotFound, InvalidAppointment
from app.exceptions.users import Forbidden
from app.models.payments import PaymentStatus
from app.models.preferences import PaymentType
from app.models.services import (
    Service,
    AppointmentSlots,
    DayOfWeek,
    AvailableAppointment as AA,
    AvailableAppointmentsForSlots as AAFS,
    Appointment,
    AppointmentCreate,
    ServiceRead,
)
from app.models.addresses import Address
from app.repositories.services import AppointmentsRepository
from app.services.services import AppointmentsService, ServicesService
from app.services.users import UsersService
from app.services.payments import PaymentsService
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
        self.users_service = AsyncMock(spec=UsersService)
        self.payments_service = AsyncMock(spec=PaymentsService)
        self.service = AppointmentsService(
            self.repository, self.services_service, self.users_service, self.payments_service
        )

    async def test_get_available_appointments_simple(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_first_no_include_partial(self) -> None:
        # Given
        now = self.get_now(time(8, 15))  # It's 8:15AM
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, include_partial=False
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

        self.assert_repo_get_all_by_range(now)
        assert available_appointments == [
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_first_one_finished(self) -> None:
        # Given
        now = self.get_now(time(8, 40))  # It's 8:40AM
        self.set_slots(now)
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_one_overlap(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                payment_status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
                customer_address_id=uuid4(),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=2,  # Only 2 availabl
                    ),
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_one_overlap_is_removed(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now, max_per_slot=1)  # Only 1 appointment per slot
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                payment_status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
                customer_address_id=uuid4(),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=1,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_one_overlap_two_times(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = [
            # this appointment overlaps with both slots,
            # which can happen if the service provider changes the
            # slots configuration after the appointment was made
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                end=datetime.combine(now.date(), time(8, 45), now.tzinfo),
                payment_status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
                customer_address_id=uuid4(),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=2,  # Only 2 available
                    ),
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=2,  # Only 2 available
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_should_get_next_week(self) -> None:
        # Given
        now = self.get_now()
        today = DayOfWeek.from_weekday(now.date().weekday())
        # I can make appointments for the next week:
        self.service_model.appointment_days_in_advance = 7
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(8, 30),
                end_day=today,
                appointment_price=Decimal(50),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                    AA(
                        start=datetime.combine(next_week, time(8, 0), now.tzinfo),
                        end=datetime.combine(next_week, time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_should_get_next_week_with_overlap(self) -> None:
        # Given
        now = self.get_now()
        # I can make appointments for the next week:
        self.set_slots(now, advance=7, end=time(8, 30))
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                end=datetime.combine(now.date(), time(8, 45), now.tzinfo),
                payment_status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
                customer_address_id=uuid4(),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=2,
                    ),
                    AA(
                        start=datetime.combine(next_week, time(8, 0), now.tzinfo),
                        end=datetime.combine(next_week, time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                ],
            )
        ]

    async def test_get_available_appointments_many_slots(self) -> None:
        # Given
        now = self.get_now()
        today = DayOfWeek.from_weekday(now.date().weekday())
        tomorrow = DayOfWeek.from_weekday((now.date() + timedelta(days=1)).weekday())
        self.service_model.appointment_days_in_advance = 1
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_price=Decimal(50),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            ),
            AAFS(
                slots_configuration=self.service_model.appointment_slots[1],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(13, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(13, 45), now.tzinfo),
                        amount=1,
                    )
                ],
            ),
            AAFS(
                slots_configuration=self.service_model.appointment_slots[2],
                available_appointments=[
                    AA(
                        start=datetime.combine(tomorrow_date, time(10, 0), now.tzinfo),
                        end=datetime.combine(tomorrow_date, time(14, 0), now.tzinfo),
                        amount=2,
                    ),
                    AA(
                        start=datetime.combine(tomorrow_date, time(14, 0), now.tzinfo),
                        end=datetime.combine(tomorrow_date, time(18, 0), now.tzinfo),
                        amount=2,
                    ),
                ],
            ),
        ]

    async def test_get_available_appointments_many_slots_with_overlap(self) -> None:
        # Given
        now = self.get_now()
        today = DayOfWeek.from_weekday(now.date().weekday())
        tomorrow = DayOfWeek.from_weekday((now.date() + timedelta(days=1)).weekday())
        self.service_model.appointment_days_in_advance = 1
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=time(8, 0),
                end_time=time(9, 0),
                end_day=today,
                appointment_price=Decimal(50),
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
                start=datetime.combine(now.date(), time(13, 30), now.tzinfo),
                end=datetime.combine(tomorrow_date, time(14, 00), now.tzinfo),
                payment_status=PaymentStatus.IN_PROGRESS,
                customer_id=uuid4(),
                customer_address_id=uuid4(),
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
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 0), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            ),
            AAFS(
                slots_configuration=self.service_model.appointment_slots[2],
                available_appointments=[
                    AA(
                        start=datetime.combine(tomorrow_date, time(10, 0), now.tzinfo),
                        end=datetime.combine(tomorrow_date, time(14, 0), now.tzinfo),
                        amount=1,
                    ),
                    AA(
                        start=datetime.combine(tomorrow_date, time(14, 0), now.tzinfo),
                        end=datetime.combine(tomorrow_date, time(18, 0), now.tzinfo),
                        amount=2,
                    ),
                ],
            ),
        ]

    async def test_get_available_appointments_with_after(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        after = datetime.combine(now.date(), time(8, 30), now.tzinfo)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, after=after
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=after)
        assert available_appointments == [
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            ),
        ]

    async def test_get_available_appointments_with_before(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        before = datetime.combine(now.date(), time(8, 30), now.tzinfo)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, before=before
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, before=before)
        assert available_appointments == [
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 00), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                ],
            ),
        ]

    async def test_get_available_appointments_with_before_partial(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        before = datetime.combine(now.date(), time(8, 45), now.tzinfo)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, before=before
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, before=before)
        assert available_appointments == [
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 00), now.tzinfo),
                        end=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        amount=3,
                    ),
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=3,
                    ),
                ],
            ),
        ]

    async def test_get_available_appointments_with_after_and_overlap(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = [
            Appointment(
                start=datetime.combine(now.date(), time(7, 0), now.tzinfo),
                end=datetime.combine(now.date(), time(8, 45), now.tzinfo),
                payment_status=PaymentStatus.COMPLETED,
                customer_id=uuid4(),
                customer_address_id=uuid4(),
            )
        ]
        self.services_service.get_service_by_id.return_value = self.service_model

        # When
        after = datetime.combine(now.date(), time(8, 40), now.tzinfo)
        available_appointments = await self.service.get_available_appointments(
            self.service_model.id, now=now, after=after
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=after)
        assert available_appointments == [
            AAFS(
                slots_configuration=self.service_model.appointment_slots[0],
                available_appointments=[
                    AA(
                        start=datetime.combine(now.date(), time(8, 30), now.tzinfo),
                        end=datetime.combine(now.date(), time(9, 0), now.tzinfo),
                        amount=2,
                    ),
                ],
            ),
        ]

    async def test_create_appointment_unmet_payment_conditions_should_raise(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model
        self.payments_service.check_payment_conditions.side_effect = ValueError

        # When, Then
        start = datetime.combine(now.date(), time(8, 00), now.tzinfo)
        customer_id = uuid4()
        address_id = uuid4()
        with pytest.raises(ValueError):
            await self.service.create_appointment(
                AppointmentCreate(start=start),
                self.service_model.id,
                customer_id,
                address_id,
                "token",
                now=now,
            )
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.payments_service.check_payment_conditions.assert_called_once_with(
            self.service_model, customer_id, address_id, "token"
        )
        self.repository.save.assert_not_called()

    async def test_create_appointment_invalid_start_time_should_raise(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model

        # When, Then
        start = datetime.combine(now.date(), time(8, 15), now.tzinfo)
        customer_id = uuid4()
        address_id = uuid4()
        with pytest.raises(InvalidAppointment):
            await self.service.create_appointment(
                AppointmentCreate(start=start),
                self.service_model.id,
                customer_id,
                address_id,
                "token",
                now=now,
            )
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=start)
        self.repository.save.assert_not_called()

    async def test_create_appointment(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model
        image_url = "http://image.url"
        self.services_service.get_services_read.return_value = [
            ServiceRead(
                address=self.service_model.address,
                appointment_slots=self.service_model.appointment_slots,
                image_url=image_url,
                **self.service_model.model_dump()
            )
        ]
        self.repository.save.side_effect = lambda x: x

        token = "token"
        result_url = "result url"
        self.payments_service.create_preference.return_value = result_url

        service_reference: str
        fee = (
            settings.FEE_PERCENTAGE
            * self.service_model.appointment_slots[0].appointment_price
            / 100
        )

        def check_payment_data(data: dict[str, Any]) -> None:
            nonlocal service_reference
            service_reference = data["service_reference"]
            pref_data = data["preference_data"]

            assert data["type"] == PaymentType.SERVICE_APPOINTMENT
            assert len(pref_data["items"]) == 1
            assert (
                pref_data["items"][0].items()
                >= {
                    "title": self.service_model.name,
                    "currency_id": "ARS",
                    "quantity": 1,
                    "unit_price": self.service_model.appointment_slots[0].appointment_price,
                    "picture_url": image_url,
                }.items()
            )
            assert pref_data["marketplace_fee"] == fee
            assert "shipments" not in pref_data
            assert pref_data["metadata"] == {
                "service_id": self.service_model.id,
                "appointment_id": service_reference,
                "type": PaymentType.SERVICE_APPOINTMENT,
            }

        # When
        start = datetime.combine(now.date(), time(8, 0), now.tzinfo)
        customer_id = uuid4()
        address_id = uuid4()
        created_appointment = await self.service.create_appointment(
            AppointmentCreate(start=start),
            self.service_model.id,
            customer_id,
            address_id,
            "token",
            now=now,
        )

        # Then
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.assert_repo_get_all_by_range(now, after=start)
        self.payments_service.check_payment_conditions.assert_called_once_with(
            self.service_model, customer_id, address_id, "token"
        )
        self.payments_service.create_preference.assert_called_once_with(
            CustomMatcher(check_payment_data), self.service_model.owner_id, token
        )
        self.repository.save.assert_called_once_with(created_appointment)
        assert created_appointment.payment_status == PaymentStatus.CREATED
        assert created_appointment.start == datetime.combine(now.date(), time(8, 0), now.tzinfo)
        assert created_appointment.end == datetime.combine(now.date(), time(8, 30), now.tzinfo)
        assert created_appointment.service_id == self.service_model.id
        assert created_appointment.customer_id == customer_id
        assert created_appointment.payment_url == result_url
        assert created_appointment.id == service_reference

    async def test_create_appointment_payment_exception(self) -> None:
        # Given
        now = self.get_now()
        self.set_slots(now)
        self.repository.get_all_by_range.return_value = []
        self.services_service.get_service_by_id.return_value = self.service_model
        image_url = "http://image.url"
        self.services_service.get_services_read.return_value = [
            ServiceRead(
                address=self.service_model.address,
                appointment_slots=self.service_model.appointment_slots,
                image_url=image_url,
                **self.service_model.model_dump()
            )
        ]
        self.payments_service.create_preference.side_effect = ValueError

        # When, Then
        start = datetime.combine(now.date(), time(8, 0), now.tzinfo)
        with pytest.raises(ValueError):
            await self.service.create_appointment(
                AppointmentCreate(start=start),
                self.service_model.id,
                uuid4(),
                uuid4(),
                "token",
                now=now,
            )

        self.repository.save.assert_not_called()

    async def test_invalid_appointment_status_update(self) -> None:
        # Given
        now = self.get_now()
        appointment = Appointment(
            payment_status=PaymentStatus.COMPLETED,
            payment_url=None,
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=uuid4(),
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = appointment
        self.payments_service.update_payment_status.side_effect = Forbidden

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.update_appointment_status(
                self.service_model.id, appointment.id, PaymentStatus.IN_PROGRESS
            )

        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment.id))
        self.payments_service.update_payment_status.assert_called_once_with(
            appointment, PaymentStatus.IN_PROGRESS
        )
        self.repository.save.assert_not_called()

    async def test_update_appointment_no_changes_idempotent(self) -> None:
        # Given
        now = self.get_now()
        appointment = Appointment(
            payment_status=PaymentStatus.CANCELLED,
            payment_url=None,
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=uuid4(),
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = appointment
        self.payments_service.update_payment_status.return_value = False

        # When
        await self.service.update_appointment_status(
            self.service_model.id, appointment.id, PaymentStatus.CANCELLED
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment.id))
        self.payments_service.update_payment_status.assert_called_once_with(
            appointment, PaymentStatus.CANCELLED
        )
        self.repository.save.assert_not_called()

    async def test_update_appointment_ok_should_save(self) -> None:
        # Given
        now = self.get_now()
        appointment = Appointment(
            payment_status=PaymentStatus.CREATED,
            payment_url="url",
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=uuid4(),
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = appointment
        self.payments_service.update_payment_status.return_value = True

        # When
        await self.service.update_appointment_status(
            self.service_model.id, appointment.id, PaymentStatus.CANCELLED
        )

        # Then
        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment.id))
        self.payments_service.update_payment_status.assert_called_once_with(
            appointment, PaymentStatus.CANCELLED
        )
        self.repository.save.assert_called_once_with(appointment)

    async def test_get_appointment_by_service_owner_should_call_repository_get_by_id(self) -> None:
        # Given
        now = self.get_now()
        appointment = Appointment(
            payment_status=PaymentStatus.CREATED,
            payment_url="url",
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=uuid4(),
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = appointment

        # When
        saved_record = await self.service.get_appointment(
            self.service_model.id, appointment.id, self.service_model.owner_id
        )

        # Then
        assert saved_record == appointment
        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment.id))

    async def test_get_appointment_by_customer_should_call_repository_get_by_id(self) -> None:
        # Given
        now = self.get_now()
        customer_id = uuid4()
        appointment = Appointment(
            payment_status=PaymentStatus.CREATED,
            payment_url="url",
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=customer_id,
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = appointment

        # When
        saved_record = await self.service.get_appointment(
            self.service_model.id, appointment.id, customer_id
        )

        # Then
        assert saved_record == appointment
        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment.id))

    async def test_get_appointment_unrelated_user_should_raise(self) -> None:
        # Given
        now = self.get_now()
        appointment = Appointment(
            payment_status=PaymentStatus.CREATED,
            payment_url="url",
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=uuid4(),
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.repository.get_by_id.return_value = appointment

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.get_appointment(self.service_model.id, appointment.id, uuid4())

        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment.id))

    async def test_get_appointment_not_exists_should_raise(self) -> None:
        # Given
        appointment_id = uuid4()
        self.repository.get_by_id.return_value = None

        # When, Then
        with pytest.raises(AppointmentNotFound):
            await self.service.get_appointment(self.service_model.id, appointment_id, uuid4())

        self.repository.get_by_id.assert_called_once_with((self.service_model.id, appointment_id))

    async def test_get_service_appointments_unrelated_user_should_raise(self) -> None:
        # Given
        self.services_service.get_service_by_id.return_value = self.service_model

        # When, Then
        with pytest.raises(Forbidden):
            await self.service.get_service_appointments(self.service_model.id, uuid4(), 5, 5)

        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)

    async def test_get_service_appointments_service_owner_user_should_return(self) -> None:
        # Given
        now = self.get_now()
        appointment = Appointment(
            payment_status=PaymentStatus.CREATED,
            payment_url="url",
            start=now,
            end=now + timedelta(minutes=30),
            service_id=self.service_model.id,
            customer_id=uuid4(),
            service=self.service_model,
            customer_address_id=uuid4(),
        )
        self.services_service.get_service_by_id.return_value = self.service_model
        self.repository.get_all_by_range.return_value = [appointment]
        self.repository.count_all.return_value = 1

        # When
        appointments, total = await self.service.get_service_appointments(
            self.service_model.id, self.service_model.owner_id, 5, 0
        )

        # Then
        assert total == 1
        assert appointments[0] == appointment
        self.services_service.get_service_by_id.assert_called_once_with(self.service_model.id)
        self.repository.get_all_by_range.assert_called_once_with(
            None, None, True, 5, 0, service_id=self.service_model.id
        )
        self.repository.count_all.assert_called_once_with(service_id=self.service_model.id)

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
            return_partial=True,
            service_id=self.service_model.id,
            payment_status=CustomMatcher[list[PaymentStatus]](
                lambda s: len(set(s)) == 3 and PaymentStatus.CANCELLED not in s
            ),
        )

    def set_slots(
        self,
        now: datetime,
        start: time = time(8, 0),
        end: time = time(9, 0),
        advance: int = 0,
        max_per_slot: int = 3,
    ) -> None:
        today = DayOfWeek.from_weekday(now.date().weekday())
        self.service_model.appointment_days_in_advance = advance
        self.service_model.appointment_slots = [
            AppointmentSlots(
                start_day=today,
                start_time=start,
                end_time=end,
                end_day=today,
                appointment_price=Decimal(50),
                appointment_duration=timedelta(minutes=30),
                max_appointments_per_slot=max_per_slot,
            )
        ]

    def get_now(self, t: time = time(1, 0)) -> datetime:
        tz = ZoneInfo(self.service_model.timezone)
        now = datetime.combine(date.today(), t, tz)
        return now
