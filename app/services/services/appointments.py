from datetime import datetime, timedelta, time, date
from typing import Generator, Iterable, Sequence
from zoneinfo import ZoneInfo
import logging

from fastapi import Depends
from intervaltree import IntervalTree  # type: ignore

from app.config import settings
from app.exceptions.appointments import AppointmentNotFound, InvalidAppointment
from app.exceptions.users import Forbidden
from app.models.preferences import PaymentType, PreferenceItem, ServiceAppointmentPaymentData
from app.models.services import (
    Appointment,
    AppointmentCreate,
    AvailableAppointment,
    AppointmentSlots,
    AppointmentSlotsBase,
    Service,
    AvailableAppointmentsForSlots,
    AvailableAppointmentsList,
)
from app.models.util import Id
from app.models.payments import PaymentStatus, PaymentStatusUpdate
from app.repositories.services import AppointmentsRepository
from ..users import UsersService
from ..payments import PaymentsService
from .services import ServicesService


class AppointmentsService:
    def __init__(
        self,
        appointments_repo: AppointmentsRepository = Depends(),
        services_service: ServicesService = Depends(),
        users_service: UsersService = Depends(),
        payments_service: PaymentsService = Depends(),
    ):
        self.appointments_repo = appointments_repo
        self.services_service = services_service
        self.users_service = users_service
        self.payments_service = payments_service

    async def create_appointment(
        self,
        data: AppointmentCreate,
        service_id: Id,
        customer_id: Id,
        user_address_id: Id,
        token: str,
        *,
        now: datetime | None = None,
    ) -> Appointment:
        service = await self.services_service.get_service_by_id(service_id)
        start = service.to_tz(data.start)
        logging.debug(f"Creating appointment for service {service_id} at {start}")

        await self.payments_service.check_payment_conditions(
            service, customer_id, user_address_id, token
        )

        available_appointments = await self.get_available_appointments(
            service, after=start, now=now
        )

        for slots_config, available_appointment in available_appointments.iterate_appointments():
            if available_appointment.start == start:
                break
        else:
            logging.debug(f"No available appointment found for {service_id} at {start}")
            raise InvalidAppointment

        appointment = Appointment(
            start=start,
            end=available_appointment.end,
            payment_status=PaymentStatus.CREATED,
            service_id=service_id,
            customer_id=customer_id,
            customer_address_id=user_address_id,
        )

        payment_data = await self.__build_order(service, appointment, slots_config)
        appointment.payment_url = await self.payments_service.create_preference(
            payment_data, service.owner_id, token
        )
        return await self.appointments_repo.save(appointment)

    async def get_available_appointments(
        self,
        service: Id | Service,
        *,
        after: datetime | None = None,
        before: datetime | None = None,
        now: datetime | None = None,
    ) -> AvailableAppointmentsList:
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

        now = service.to_tz(now) if now else datetime.now(ZoneInfo(service.timezone))
        after = max(now, service.to_tz(after)) if after else now
        max_start = self.__get_max_allowed_appointment_start(service, now)
        before = min(max_start, service.to_tz(before)) if before else max_start

        today = now.date()
        appointments = await self.__get_open_appointments_in_range(service.id, after, before)
        appointments_tree = IntervalTree.from_tuples((a.start, a.end) for a in appointments)
        available_appointments = AvailableAppointmentsList()
        for d in range(0, service.appointment_days_in_advance + 1):
            current_date = today + timedelta(days=d)
            self.__merge_or_extend_available(
                available_appointments,
                self.__date_available_appointments(
                    current_date, after, before, appointments_tree, slots_per_day
                ),
            )
        return available_appointments

    async def update_appointment_status(
        self, service_id: Id, appointment_id: Id, new_status: PaymentStatusUpdate
    ) -> None:
        appointment = await self.appointments_repo.get_by_id((service_id, appointment_id))
        if appointment is None:
            raise AppointmentNotFound

        if not await self.payments_service.update_payment_status(appointment, new_status):
            return

        await self.appointments_repo.save(appointment)

    async def get_appointment(self, service_id: Id, appointment_id: Id, user_id: Id) -> Appointment:
        appointment = await self.appointments_repo.get_by_id((service_id, appointment_id))
        if appointment is None:
            raise AppointmentNotFound
        if user_id not in (appointment.customer_id, appointment.service.owner_id):
            raise Forbidden
        return appointment

    async def get_service_appointments(
        self, service_id: Id, user_id: Id, limit: int, skip: int
    ) -> tuple[Sequence[Appointment], int]:
        service = await self.services_service.get_service_by_id(service_id)
        if user_id != service.owner_id:
            raise Forbidden
        appointments = await self.appointments_repo.get_all(
            service_id=service_id, limit=limit, skip=skip
        )
        amount = await self.appointments_repo.count_all(service_id=service_id)
        return appointments, amount

    async def get_user_appointments(
        self, user_id: Id, limit: int, skip: int
    ) -> tuple[Sequence[Appointment], int]:
        appointments = await self.appointments_repo.get_all(
            customer_id=user_id, limit=limit, skip=skip
        )
        amount = await self.appointments_repo.count_all(customer_id=user_id)
        return appointments, amount

    def __merge_or_extend_available(
        self,
        available_appointments: AvailableAppointmentsList,
        new_available_appointments: Iterable[AvailableAppointmentsForSlots],
    ) -> None:
        """
        Adds the new available appointments to the list of available appointments.
        If two available appointments have the same slots configuration, the available
        appointments for that slot are merged. This might happen when the only available
        appointments are for the same slots configuration but in different weeks.
        """
        last = available_appointments[-1] if available_appointments else None
        for available in new_available_appointments:
            if last and last.slots_configuration == available.slots_configuration:
                last.available_appointments.extend(available.available_appointments)
            else:
                available_appointments.append(available)
                last = available

    def __date_available_appointments(
        self,
        start_date: date,
        after: datetime,
        before: datetime,
        tree: IntervalTree,
        slots_per_day: dict[int, list[AppointmentSlots]],
    ) -> Generator[AvailableAppointmentsForSlots, None, None]:
        """
        Returns the available appointments for each slots configuration in the given date.

        `start_date` is the date in which the returned available appointments start.
        `after` and `before` are used to filter the returned available appointments. Only
        appointments that take place (totally or partially) in between `after` and `before` will be
        returned.
        `tree` contains the (start, end) intervals of the existing non-cancelled appointments
        `slots_per_day` is a dictionary that maps the weekday to the appointment slots that start on
        that day.
        """
        day_slots = slots_per_day.get(start_date.weekday(), ())

        for slots in day_slots or ():
            available_for_these_slots = list(
                self.__date_slots_available_appointments(start_date, slots, after, before, tree)
            )
            if available_for_these_slots:
                yield AvailableAppointmentsForSlots(
                    slots_configuration=slots,
                    available_appointments=available_for_these_slots,
                )

    def __date_slots_available_appointments(
        self,
        start_date: date,
        slots: AppointmentSlots,
        after: datetime,
        before: datetime,
        tree: IntervalTree,
    ) -> Generator[AvailableAppointment, None, None]:
        """
        Returns the available appointments for the given appointment slots and date,

        `start_date` is the date in which the returned available appointments start.
        `slots` is the appointment slots configuration for which the available appointments will be
        returned, and must take place in the given date.
        `after` and `before` are used to filter the returned available appointments. Only
        appointments that take place (totally or partially) in between `after` and `before` will be
        returned.
        `tree` contains the (start, end) intervals of the existing non-cancelled appointments,
        """
        slots_end = datetime.combine(start_date, slots.end_time, tzinfo=after.tzinfo)
        start = datetime.combine(start_date, slots.start_time, tzinfo=after.tzinfo)
        end = start + slots.appointment_duration
        while end <= slots_end:
            if end > after and start < before:
                amount = slots.max_appointments_per_slot - len(tree.overlap(start, end))
                if amount > 0:
                    yield AvailableAppointment(start=start, end=end, amount=amount)
            start = end
            end += slots.appointment_duration

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
            payment_status=[
                PaymentStatus.CREATED,
                PaymentStatus.IN_PROGRESS,
                PaymentStatus.COMPLETED,
            ],
        )

    async def __build_order(
        self, service: Service, appointment: Appointment, used_slot: AppointmentSlotsBase
    ) -> ServiceAppointmentPaymentData:
        item = await self.__build_order_item(service, appointment, used_slot)
        fee = settings.FEE_PERCENTAGE * item["unit_price"] * item["quantity"] / 100
        return {
            "type": PaymentType.SERVICE_APPOINTMENT,
            "service_reference": appointment.id,
            "preference_data": {
                "items": [item],
                "marketplace_fee": fee,
                "metadata": {
                    "appointment_id": appointment.id,
                    "service_id": service.id,
                    "type": PaymentType.SERVICE_APPOINTMENT,
                },
            },
        }

    async def __build_order_item(
        self, service: Service, appointment: Appointment, used_slot: AppointmentSlotsBase
    ) -> PreferenceItem:
        tz = ZoneInfo(service.timezone)
        service_read = (await self.services_service.get_services_read(service))[0]
        return {
            "title": service.name,
            "currency_id": "ARS",
            "picture_url": service_read.image_url,
            "description": appointment.start.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
            "quantity": 1,
            "unit_price": used_slot.appointment_price,
        }
