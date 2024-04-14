from datetime import datetime

from fastapi import APIRouter, status, Depends, Query
from pydantic import AwareDatetime

from app.auth import get_caller_id, get_caller_token
from app.models.services import AppointmentRead, AppointmentCreate, AvailableAppointmentsForSlots
from app.models.util import Id
from app.routes.responses.auth import FORBIDDEN
from app.serializers.services import AppointmentList
from app.services.services import AppointmentsService
from ..responses.services import SERVICE_NOT_FOUND_ERROR
from ..responses.appointments import (
    APPOINTMENT_NOT_FOUND_ERROR,
    INVALID_APPOINTMENT_ERROR,
)
from ..responses.payments import (
    COLLECTOR_NOT_READY,
    CANT_BUY_FROM_OWN_BUSINESS,
    OUTSIDE_BUSINESS_RANGE,
)
from ..util import get_exception_docs


router = APIRouter(prefix="", tags=["Service appointments"])


@router.post(
    "/services/{service_id}/appointments",
    status_code=status.HTTP_201_CREATED,
    responses=get_exception_docs(
        SERVICE_NOT_FOUND_ERROR,
        INVALID_APPOINTMENT_ERROR,
        COLLECTOR_NOT_READY,
        CANT_BUY_FROM_OWN_BUSINESS,
        OUTSIDE_BUSINESS_RANGE,
    ),
)
async def create_appointment(
    data: AppointmentCreate,
    service_id: Id,
    user_address_id: Id,
    appointments_service: AppointmentsService = Depends(),
    user_id: Id = Depends(get_caller_id),
    token: str = Depends(get_caller_token),
) -> AppointmentRead:
    return await appointments_service.create_appointment(
        data, service_id, user_id, user_address_id, token
    )


@router.get("/services/appointments/me")
async def get_my_appointments(
    user_id: Id = Depends(get_caller_id),
    after: AwareDatetime | None = Query(None),
    before: AwareDatetime | None = Query(None),
    include_partial: bool = Query(True),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    appointments_service: AppointmentsService = Depends(),
) -> AppointmentList:
    appointments, count = await appointments_service.get_user_appointments(
        user_id, limit, offset, after, before, include_partial
    )
    return AppointmentList(appointments=appointments, amount=count)


@router.get(
    "/services/{service_id}/appointments", responses=get_exception_docs(SERVICE_NOT_FOUND_ERROR)
)
async def get_service_appointments(
    service_id: Id,
    after: AwareDatetime | None = Query(None),
    before: AwareDatetime | None = Query(None),
    include_partial: bool = Query(True),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    user_id: Id = Depends(get_caller_id),
    appointments_service: AppointmentsService = Depends(),
) -> AppointmentList:
    appointments, count = await appointments_service.get_service_appointments(
        service_id, user_id, limit, offset, after, before, include_partial
    )
    return AppointmentList(appointments=appointments, amount=count)


@router.get(
    "/services/{service_id}/appointments/available",
    responses=get_exception_docs(SERVICE_NOT_FOUND_ERROR),
)
async def get_available_appointments(
    service_id: Id,
    after: datetime | None = Query(None),
    before: datetime | None = Query(None),
    include_partial: bool = Query(True),
    appointments_service: AppointmentsService = Depends(),
) -> list[AvailableAppointmentsForSlots]:
    return await appointments_service.get_available_appointments(
        service_id, after=after, before=before, include_partial=include_partial
    )


@router.get(
    "/services/{service_id}/appointments/{appointment_id}",
    responses=get_exception_docs(FORBIDDEN, APPOINTMENT_NOT_FOUND_ERROR),
)
async def get_service_appointment(
    service_id: Id,
    appointment_id: Id,
    appointments_service: AppointmentsService = Depends(),
    user_id: Id = Depends(get_caller_id),
) -> AppointmentRead:
    return await appointments_service.get_appointment(service_id, appointment_id, user_id)
