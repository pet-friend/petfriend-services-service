import logging

from fastapi import Depends, status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient, Timeout, URL

from app.exceptions.payments import CantBuyFromOwnBusiness, CollectorNotReady, OutsideBusinessRange
from app.exceptions.users import Forbidden
from app.models.addresses import Address
from app.models.preferences import PaymentData
from app.models.services.services import Service
from app.models.stores import Store
from app.models.payments import PaymentStatus, PaymentStatusModel, PaymentStatusUpdate
from app.models.util import Id
from app.config import settings
from .users import UsersService

REQUEST_TIMEOUT = Timeout(5, read=45)
FORBIDDEN_STATUS_CHANGES = [PaymentStatus.COMPLETED, PaymentStatus.CANCELLED]


class PaymentsService:
    def __init__(
        self,
        users_service: UsersService = Depends(),
    ):
        self.users_service = users_service

    async def update_payment_status(
        self, model: PaymentStatusModel, new_status: PaymentStatusUpdate
    ) -> bool:
        """
        Updates the status of a payment and returns True if the status was updated.
        """
        if model.payment_status == new_status:
            # No update
            return False

        if model.payment_status in FORBIDDEN_STATUS_CHANGES:
            logging.warning(
                f"Tried to update status of payment from '{model.payment_status}' to '{new_status}'"
            )
            raise Forbidden

        model.payment_status = new_status
        model.payment_url = None
        return True

    async def check_payment_conditions(
        self, s: Store | Service, user_id: Id, user_address_id: Id, token: str
    ) -> None:
        if s.owner_id == user_id:
            raise CantBuyFromOwnBusiness

        user_coords = await self.users_service.get_user_address_coordinates(
            user_id, user_address_id, token
        )

        store_address: Address = s.address
        if not user_coords.within(store_address, s.range_km):
            raise OutsideBusinessRange

    async def create_preference(
        self, data: PaymentData, user_to_be_payed_id: Id, token: str
    ) -> str:
        """
        Creates a payment preference using the payment service and returns the preference URL.
        """
        async with AsyncClient(
            headers={"Authorization": f"Bearer {token}"}, timeout=REQUEST_TIMEOUT
        ) as client:
            url = URL(
                settings.PAYMENTS_SERVICE_URL + "/payment",
                params={
                    "user_to_be_payed_id": str(user_to_be_payed_id),
                },
            )
            r = await client.post(url, json=jsonable_encoder(data))
            if r.status_code == status.HTTP_404_NOT_FOUND:
                raise CollectorNotReady
            logging.debug(f"Payment service response: {r.status_code} {r.text}")
            r.raise_for_status()
            preference_url: str = r.json()
            return preference_url
