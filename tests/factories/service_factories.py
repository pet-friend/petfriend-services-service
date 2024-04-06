from datetime import time, timedelta

from polyfactory.factories.pydantic_factory import ModelFactory

from app.models.addresses import AddressCreate
from app.models.services import ServiceCreate, DayOfWeek, AppointmentSlotsBase
from .address_factories import AddressCreateFactory


class ServiceCreateFactory(ModelFactory[ServiceCreate]):
    __model__ = ServiceCreate

    @classmethod
    def appointment_slots(cls) -> list[AppointmentSlotsBase]:
        all_days: list[DayOfWeek] = list(DayOfWeek)
        days = cls.__random__.sample(all_days, k=cls.__random__.randint(1, 7))
        slots = []
        for day in days:
            day_slots = cls.__random__.randint(1, 3)
            start_hours = cls.__random__.sample(range(6, 22, 3), k=day_slots)
            for start_hour in start_hours:
                duration_mins = cls.__random__.randint(5, 90)
                slots.append(
                    AppointmentSlotsBase(
                        start_day=day,
                        end_day=day,
                        start_time=time(hour=start_hour),
                        end_time=time(hour=start_hour + 2),
                        appointment_duration=timedelta(minutes=duration_mins),
                    )
                )
        return slots

    @classmethod
    def address(cls) -> AddressCreate:
        return AddressCreateFactory.build(country_code="AR", type="other")
