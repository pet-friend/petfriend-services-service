from fastapi import APIRouter, status, Depends

from app.auth import validate_payments_key
from app.models.payments import PaymentUpdate
from app.models.util import Id
from app.services.stores import PurchasesService
from app.services.services import AppointmentsService
from .responses.auth import UNAUTHORIZED
from .util import get_exception_docs


router = APIRouter(
    prefix="",
    tags=["Payment updates"],
    dependencies=[Depends(validate_payments_key)],
    responses=get_exception_docs(UNAUTHORIZED),
)


@router.patch(
    "/stores/{store_id}/purchases/{purchase_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_purchase_status(
    update: PaymentUpdate,
    store_id: Id,
    purchase_id: Id,
    purchases_service: PurchasesService = Depends(),
) -> None:
    await purchases_service.update_purchase_status(store_id, purchase_id, update.status)


@router.patch(
    "/services/{service_id}/appointments/{appointment_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_appointment_status(
    update: PaymentUpdate,
    service_id: Id,
    appointment_id: Id,
    appointments_service: AppointmentsService = Depends(),
) -> None:
    await appointments_service.update_appointment_status(service_id, appointment_id, update.status)
