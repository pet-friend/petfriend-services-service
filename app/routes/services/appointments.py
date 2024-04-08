# from datetime import datetime

from fastapi import APIRouter

# , status, Depends, Query

# from app.auth import get_caller_id
# from app.models.services import AppointmentRead, AppointmentCreate, AvailableAppointment
# from app.models.util import Id
# from app.services.services import AppointmentsService
# from ..responses.services import SERVICE_NOT_FOUND_ERROR
# from ..util import get_exception_docs


router = APIRouter(prefix="/services/{service_id}/appointments", tags=["Service appointments"])


# @router.post(
#     "",
#     status_code=status.HTTP_201_CREATED,
#     responses=get_exception_docs(SERVICE_NOT_FOUND_ERROR),
# )
# async def create_service(
#     data: AppointmentCreate,
#     service_id: Id,
#     appointments_service: AppointmentsService = Depends(),
#     customer_id: Id = Depends(get_caller_id),
# ) -> AppointmentRead:
#     return await appointments_service.create_appointment(data, service_id, customer_id)


# @router.post(
#     "/available",
#     responses=get_exception_docs(SERVICE_NOT_FOUND_ERROR),
# )
# async def get_available_appointments(
#     service_id: Id,
#     after: datetime | None = Query(None),
#     before: datetime | None = Query(None),
#     appointments_service: AppointmentsService = Depends(),
# ) -> list[AvailableAppointment]:
#     return await appointments_service.get_available_appointments(
#         service_id, after=after, before=before
#     )
