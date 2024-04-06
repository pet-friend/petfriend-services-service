from datetime import datetime, timedelta, time, date
from typing import Generator, Sequence
from zoneinfo import ZoneInfo

from fastapi import Depends
from intervaltree import IntervalTree  # type: ignore

from app.exceptions.appointments import InvalidAppointment
from app.models.services import (
    Appointment,
    AppointmentCreate,
    AvailableAppointment,
    AppointmentSlots,
    Service,
)
from app.models.util import Id
from app.models.payments import PaymentStatus
from app.repositories.services import AppointmentsRepository
from .services import ServicesService


class AppointmentsService:
    def __init__(
        self,
        appointments_repo: AppointmentsRepository = Depends(),
        services_service: ServicesService = Depends(),
    ):
        self.appointments_repo = appointments_repo
        self.services_service = services_service

    async def create_appointment(
        self,
        data: AppointmentCreate,
        service_id: Id,
        customer_id: Id,
        *,
        now: datetime | None = None,
    ) -> Appointment:
        service = await self.services_service.get_service_by_id(service_id)
        data.start = data.start.astimezone(ZoneInfo(service.timezone))
        available_appointments = await self.get_available_appointments(
            service, after=data.start, now=now
        )

        for available_appointment in available_appointments:
            if available_appointment.start == data.start:
                break
        else:
            raise InvalidAppointment

        appointment = Appointment(
            start=data.start,
            end=available_appointment.end,
            status=PaymentStatus.CREATED,
            service_id=service_id,
            customer_id=customer_id,
        )

        return appointment

    async def get_available_appointments(
        self,
        service: Id | Service,
        *,
        after: datetime | None = None,
        before: datetime | None = None,
        now: datetime | None = None,
    ) -> list[AvailableAppointment]:
        """
        Gets the available appointments for the given service.
        The result is guaranteed to be sorted by start time.

        `after` and `before` are optional and can be used to filter returned
        available appointments. Only appointments that take place (totally or partially)
        in between `after` and `before` will be returned. Defaults to the current time and
        the maximum allowed appointment start time for the given service, respectively.

        `now` can be used to override the current time. Defaults to the current time.
        """
        if isinstance(service, Id):
            service = await self.services_service.get_service_by_id(service)
        slots_per_day: dict[int, list[AppointmentSlots]] = {}
        for slot in service.appointment_slots:
            slots_per_day.setdefault(slot.start_day.to_weekday(), []).append(slot)

        tz = ZoneInfo(service.timezone)
        now = now.astimezone(tz) if now else datetime.now(tz)
        after = max(now, after.astimezone(tz)) if after else now
        max_start = self.__get_max_allowed_appointment_start(service, now)
        before = min(max_start, before.astimezone(tz)) if before else max_start

        today = now.date()
        appointments = await self.__get_open_appointments_in_range(service.id, after, before)
        appointments_tree = IntervalTree.from_tuples((a.start, a.end) for a in appointments)
        available_appointments: list[AvailableAppointment] = []
        for d in range(0, service.appointment_days_in_advance + 1):
            current_date = today + timedelta(days=d)
            available_appointments.extend(
                self.__date_available_appointments(
                    current_date, after, before, appointments_tree, slots_per_day
                )
            )

        return available_appointments

    def __date_available_appointments(
        self,
        date: date,
        after: datetime,
        before: datetime,
        tree: IntervalTree,
        slots_per_day: dict[int, list[AppointmentSlots]],
    ) -> Generator[AvailableAppointment, None, None]:
        """
        Returns the available appointments for the given date.

        `date` is the day for which the available appointments will be returned.
        `after` and `before` are used to filter the returned available appointments. Only
        appointments that take place (totally or partially) in between `after` and `before` will be
        returned.
        `tree` contains the (start, end) intervals of the existing non-cancelled appointments
        `slots_per_day` is a dictionary that maps the weekday to the available slots for that day
        """
        day_slots = slots_per_day.get(date.weekday(), ())
        for slot in day_slots or ():
            slots_end = datetime.combine(date, slot.end_time, tzinfo=after.tzinfo)

            start = datetime.combine(date, slot.start_time, tzinfo=after.tzinfo)
            end = start + slot.appointment_duration
            while end <= slots_end:
                if end > after and start < before:
                    amount = slot.max_appointments_per_slot - len(tree.overlap(start, end))
                    if amount > 0:
                        yield AvailableAppointment(start=start, end=end, amount=amount)
                start = end
                end += slot.appointment_duration

    def __get_max_allowed_appointment_start(self, service: Service, now: datetime) -> datetime:
        """
        Return the maximum allowed appointment start time for the given service.

        `now` is the current time in the service's timezone.
        """
        today = now.date()
        return datetime.combine(
            today + timedelta(days=service.appointment_days_in_advance + 1),
            time.min,
            tzinfo=now.tzinfo,
        )

    async def __get_open_appointments_in_range(
        self, service_id: Id, range_start: datetime, range_end: datetime
    ) -> Sequence[Appointment]:
        """
        Wrapper of AppointmentsRepository.get_all_by_range that returns only
        non-cancelled appointments for the given service.
        """
        return await self.appointments_repo.get_all_by_range(
            range_start,
            range_end,
            service_id=service_id,
            status=[PaymentStatus.CREATED, PaymentStatus.IN_PROGRESS, PaymentStatus.COMPLETED],
        )
