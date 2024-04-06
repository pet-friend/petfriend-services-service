from datetime import datetime, timedelta, time, date
from typing import Generator, Sequence
from zoneinfo import ZoneInfo

from fastapi import Depends
from intervaltree import IntervalTree  # type: ignore

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

    async def create_appointmnet(self, data: AppointmentCreate, owner_id: Id) -> Appointment:
        # service = Service(
        #     **data.model_dump(exclude={"address", "appointment_slots"}),
        #     owner_id=owner_id,
        #     **(await self.__get_nested_models_from_create(data)),
        # )
        # return await self.services_repo.save(service)
        raise NotImplementedError()

    async def get_available_appointments(
        self, service_id: Id, now: datetime | None = None
    ) -> list[AvailableAppointment]:
        """
        Gets the available appointments for the given service.
        The result is guaranteed to be sorted by start time.
        """
        service = await self.services_service.get_service_by_id(service_id)

        slots_per_day: dict[int, list[AppointmentSlots]] = {}
        for slot in service.appointment_slots:
            slots_per_day.setdefault(slot.start_day.to_weekday(), []).append(slot)

        service_tz = ZoneInfo(service.timezone)
        now = now.astimezone(service_tz) if now else datetime.now(service_tz)
        until = self.__get_max_allowed_appointment_start(service, now)
        appointments = await self.__get_open_appointments_in_range(service.id, now, until)

        today = now.date()
        appointments_tree = IntervalTree.from_tuples((a.start, a.end) for a in appointments)
        available_appointments: list[AvailableAppointment] = []
        for d in range(0, service.appointment_days_in_advance + 1):
            current_date = today + timedelta(days=d)
            available_appointments.extend(
                self.__date_available_appointments(
                    current_date, now, appointments_tree, slots_per_day
                )
            )

        return available_appointments

    def __date_available_appointments(
        self,
        date: date,
        now: datetime,
        tree: IntervalTree,
        slots_per_day: dict[int, list[AppointmentSlots]],
    ) -> Generator[AvailableAppointment, None, None]:
        """
        Returns the available appointments for the given date by iterating over the slots of the day
        and decrementing the amount of available appointments for each slot that overlaps with an
        existing appointment at the same time.
        """
        day_slots = slots_per_day.get(date.weekday(), ())
        for slot in day_slots or ():
            slots_end = datetime.combine(date, slot.end_time, tzinfo=now.tzinfo)

            start = datetime.combine(date, slot.start_time, tzinfo=now.tzinfo)
            end = start + slot.appointment_duration
            while end <= slots_end:
                if end > now:
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
